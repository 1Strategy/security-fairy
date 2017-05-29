import boto3
import json
import re
import os

try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()

def lambda_handler(event, context):
<<<<<<< HEAD

    # Default API Response returns an error
    api_return_payload = {
        'statusCode': 500,
        'headers':{
            'Content-Type':'application/json'
        },
        'body':'Interal Server Error'
=======
    api_return_payload = {
        'statusCode': 500,
        'headers': {'Content-Type': 'application/json'},
        'body': 'Interal Server Error'
>>>>>>> 8595af339c53aa2226fa9b4c90f70579f85b8f33
    }

    try:

        inputs = validate_inputs(event)
        invoke_state_machine(inputs)
        api_return_payload['body'] = 'Inputs are valid.'
        api_return_payload['statusCode'] = 200

    except Exception as error:
        print(error)
        api_return_payload['body'] = "Unsuccessful:\n {error}".format(error=error)

    print(api_return_payload)
    return api_return_payload

<<<<<<< HEAD

def invoke_state_machine(inputs):
    print(json.dumps(inputs))
    # sfn_client.start_execution( stateMachineArn=os.environ['state_machine'],
    #                             input=json.dumps(inputs)



def validate_inputs(event):
=======
>>>>>>> 8595af339c53aa2226fa9b4c90f70579f85b8f33

def validate_inputs(event):
    input_payload = json.loads(event.get('body'))
    num_days = input_payload.get('num_days', 7)
    if num_days > 30 or num_days < 1:
        print(num_days)
        raise ValueError('Valid number of days is between 1 and 30 inclusive.')

<<<<<<< HEAD
    entity_arn = validate_entity_arn(input_payload.get('entity_arn'))

    return {
        'num_days': num_days,
        'entity_arn': entity_arn
    }

def validate_entity_arn(entity_arn):



        account_number = session.client('sts').get_caller_identity()["Account"]
    # Roles are valid: arn:aws:iam::842337631775:role/1S-Admins
    #                  arn:aws:sts::281782457076:assumed-role/1S-Admins/alex
    # Users are invalid: arn:aws:iam::842337631775:user/aaron

    if 'user' in entity_arn:
        raise ValueError('Users not supported. Please enter a role ARN.')

    pattern = re.compile("arn:aws:(sts|iam)+::(\d{12})?:(role|assumed-role)\/(.*)")

=======
    entity_arn = input_payload.get('entity_arn')
    pattern = re.compile("arn:aws:([a-zA-Z0-9\-])+:([a-z]{2}-[a-z]+-\d{1})?:(\d{12})?:(.*)")
>>>>>>> 8595af339c53aa2226fa9b4c90f70579f85b8f33
    if not pattern.match(entity_arn):
        raise ValueError('Invalid Resource ARN.')

    assumed_role_pattern = re.compile("arn:aws:sts::(\d{12})?:assumed-role\/(.*)\/")

    if assumed_role_pattern.match(entity_arn):
        split_arn = re.split('/|:', entity_arn)
        refactored_arn = "arn:aws:iam:" + split_arn[4] + ":role/" + split_arn[6]
        entity_arn = refactored_arn
        session.client('iam').get_role(RoleName=split_arn[6])

<<<<<<< HEAD
    return entity_arn

if __name__ == '__main__':
    lambda_handler(
    {
        'body': "{\"entity_arn\":\"arn:aws:iam::842337631775:user/aaron\",\"num_days\":7}"
    }
    ,{})
=======
if __name__ == '__main__':
    lambda_handler(
        {
            'body': "{\"entity_arn\":\"arn:aws:sts::281782457076:assumed-role/1S-Admins/alex\",\"num_days\":7}"
        }, {}
    )
>>>>>>> 8595af339c53aa2226fa9b4c90f70579f85b8f33
