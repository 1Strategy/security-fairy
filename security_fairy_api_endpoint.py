import boto3
import json
import re


def lambda_handler(event, context):
    api_return_payload = {
        'statusCode': 500,
        'headers': {'Content-Type': 'application/json'},
        'body': 'Interal Server Error'
    }

    try:

        validate_inputs(event)
        api_return_payload['body'] = 'Inputs are valid.'
        api_return_payload['statusCode'] = 200

    except Exception as error:
        print(error)
        api_return_payload['body'] = "Unsuccessful:\n {error}".format(error=error)

    print(api_return_payload)
    return api_return_payload


def validate_inputs(event):
    input_payload = json.loads(event.get('body'))
    num_days = input_payload.get('num_days', 7)
    if num_days > 30 or num_days < 1:
        print(num_days)
        raise ValueError('Valid number of days is between 1 and 30 inclusive.')

    entity_arn = input_payload.get('entity_arn')
    pattern = re.compile("arn:aws:([a-zA-Z0-9\-])+:([a-z]{2}-[a-z]+-\d{1})?:(\d{12})?:(.*)")
    if not pattern.match(entity_arn):
        raise ValueError('Invalid Resource ARN.')

    print(entity_arn)


if __name__ == '__main__':
    lambda_handler(
        {
            'body': "{\"entity_arn\":\"arn:aws:sts::281782457076:assumed-role/1S-Admins/alex\",\"num_days\":7}"
        }, {}
    )
