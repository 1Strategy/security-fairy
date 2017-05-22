import boto3
import time
from botocore.exceptions import ClientError

# Create AWS session
try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()

# TODO DynamoDB Handler

def lambda_handler(event, context):
    api_return_payload = {
        'statusCode': 500,
        'headers':{'Content-Type':'text/html'},
        'body':'Interal Server Error'
    }


    try:

        token = event.get('token')
        apply_revised_policy(token)

        api_return_payload['body'] = 'Policies applied.'
        api_return_payload['statusCode'] = 200

    except Exception as error:

        print(error)
        api_return_payload['body'] = "Unsuccessful:\n {error}".format(error=error)

    return api_return_payload

# TODO Apply new policy from DynamoDB
def apply_revised_policy(token):

    policies = get_policies(token)
    raise ValueError('Token has expired. Security-fairy must be rerun.')

# TODO Get policies from DynamoDB
def get_policies(token):

    return {}
