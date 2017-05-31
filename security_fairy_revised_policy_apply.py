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
        'headers': {'Content-Type': 'text/html'},
        'body': 'Interal Server Error'
    }



    try:
        token = event['token']
        apply_revised_policy(token)

        api_return_payload['body'] = 'Policies applied.'
        api_return_payload['statusCode'] = 200

    except Exception as error:
        print(error)
        api_return_payload['body'] = "Unsuccessful:\n {error}".format(error=error)

    return api_return_payload

# TODO Apply new policy from DynamoDB


def apply_revised_policy(token):

    policies = get_revised_policy(token)

    session.client('iam')

def get_revised_policy(token):

    try:
        policy = session.client('dynamodb', region_name = 'us-west-2') \
                        .get_item(  TableName='security_fairy_pending_approval',
                                    Key={
                                        "token":{
                                            "S": token
                                            }
                                        }
                                 )['Item']['new_policy']['S']
        print(policy)
        return policy
    except Exception as e:
        print(e)
        raise ValueError('Token doesn\'t exist or has expired. Security-fairy must be rerun.')



if __name__ == '__main__':
    get_revised_policy('8d544e31-37af-4eb2-acf3-b5eda9f108bd')
