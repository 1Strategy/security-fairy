import boto3
import os

try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()

def lambda_handler(event,context):

    sfn_client = session.client('stepfunctions')
    response = sfn_client.get_activity_task(activityArn=os.environ['activity_arn'])
    return response
