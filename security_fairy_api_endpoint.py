import boto3
import json
import re
import os

def lambda_handler(event, context):

    # Default API Response returns an error
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
        print(error)
        api_return_payload['body'] = "Unsuccessful:\n {error}".format(error=error)

    print(api_return_payload)
    return api_return_payload


def invoke_state_machine(inputs):
    print(json.dumps(inputs))
    sfn_client.start_execution( stateMachineArn=os.environ['state_machine'],
                                input=json.dumps(inputs)



def validate_inputs(event):

    input_payload = json.loads(event.get('body'))

    num_days = input_payload.get('num_days', 7)
    if num_days > 30 or num_days < 1:
        print(num_days)
        raise ValueError('Valid number of days is between 1 and 30 inclusive.')

    entity_arn = input_payload.get('entity_arn')

    pattern = re.compile("arn:aws:(sts|iam)+::(\d{12})?:(role|assumed-role)\/(.*)")

    # Roles are valid: arn:aws:iam::842337631775:role/1S-Admins
    #                  arn:aws:sts::281782457076:assumed-role/1S-Admins/alex
    # Users are invalid: arn:aws:iam::842337631775:user/aaron

    if not pattern.match(entity_arn):
        raise ValueError('Invalid Resource ARN.')

    return {
        'num_days': num_days,
        'entity_arn': entity_arn
    }



if __name__ == '__main__':
    lambda_handler(
    {
        'body': "{\"entity_arn\":\"arn:aws:sts::281782457076:assumed-role/1S-Admins/alex\",\"num_days\":7}"
    }
    ,{})
