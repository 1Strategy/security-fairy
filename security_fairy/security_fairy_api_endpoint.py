"""API Endpoint

Validates inputs to the Security Fairy tool,
then creates and executes the State Machine
which orchestrates the Security Fairy
Lambda functions.
"""


import json
import re
import os
import boto3
from botocore.exceptions import ProfileNotFound

try:
    SESSION = boto3.session.Session(profile_name='training')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


def lambda_handler(event, context):
    """ Executed by the Lambda service.

    Returns the validated inputs and invokes
    the State Machine that orchestrates
    Security Fairy.
    """

    api_return_payload = {
        'statusCode': 500,
        'headers':{
            'Content-Type':'application/json'
        },
        'body':'Interal Server Error'
    }

    try:
        inputs = validate_inputs(event)
        invoke_state_machine(inputs)
        api_return_payload['body'] = 'Inputs are valid.'
        api_return_payload['statusCode'] = 200

    except Exception as error:
        print error
        api_return_payload['body'] = "Unsuccessful:\n {error}".format(error=error)

    print api_return_payload
    return api_return_payload


def invoke_state_machine(inputs):
    """Invoke state machine"""
    print json.dumps(inputs)
    sfn_client = SESSION.client('stepfunctions')
    response = sfn_client.start_execution(stateMachineArn=os.environ['state_machine'],
                                          input=json.dumps(inputs)
                                         )
    print response


def validate_inputs(event):
    """Validate inputs"""
    input_payload = json.loads(event['body'])
    num_days = validate_date_window(input_payload.get('num_days', 7))
    entity_arn = validate_entity_arn(input_payload.get('entity_arn'))

    return {
        'num_days'  : num_days*-1,
        'entity_arn': entity_arn
    }


def validate_date_window(days):
    """Validate the date range for the Security Fairy query"""
    window = abs(days)
    if window > 30 or window < 1:
        print window
        raise ValueError('Valid number of days is between 1 and 30 inclusive.')

    return window


def validate_entity_arn(entity_arn):
    """Validate entity ARN"""

    # account_number = SESSION.client('sts').get_caller_identity()["Account"]
    # Roles are valid: arn:aws:iam::842337631775:role/1S-Admins
    #                  arn:aws:sts::281782457076:assumed-role/1S-Admins/alex
    # Users are invalid: arn:aws:iam::842337631775:user/aaron

    if 'user' in entity_arn:
        raise ValueError('Users not supported. Please enter a role ARN.')

    if 'group' in entity_arn:
        raise ValueError('Groups not supported. Please enter a role ARN.')

    pattern = re.compile("arn:aws:(sts|iam)::(\d{12})?:(role|assumed-role)\/(.*)")

    if not pattern.match(entity_arn):
        raise ValueError('Invalid Resource ARN.')

    assumed_role_pattern = re.compile("arn:aws:sts::(\d{12})?:assumed-role\/(.*)\/(.*)")

    if not assumed_role_pattern.match(entity_arn):

        split_arn = re.split('/|:', entity_arn)
        refactored_arn = "arn:aws:sts:" + split_arn[4] + ":assumed-role/" + split_arn[6]
        entity_arn = refactored_arn
        SESSION.client('iam').get_role(RoleName=split_arn[6])

    return entity_arn


if __name__ == '__main__':
    lambda_handler(
        {
            'body': "{\"entity_arn\":\"arn:aws:sts::281782457076:role/1S-Admins\",\"num_days\":30}"
        }, {}
    )
