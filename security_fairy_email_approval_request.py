
import boto3
import json
import datetime


try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()

# Use the Boto3 SDK to create a client to call SNS functions

def lambda_handler(event, context):


    execution_id = event['execution_id']
    task_token = event['task-token']
    api_endpoint = "https://byv5cb80g2.execute-api.us-west-2.amazonaws.com/prod"

    approval_url = '{api_endpoint}/approve?execution_id={execution_id}&task-token={tasktoken}' \
                        .format(api_endpoint=api_endpoint,execution_id=execution_id, tasktoken = task_token)


    sns_client = session.client('sns')
    sns_arn =  "arn:aws:sns:us-west-2:281782457076:security_fairy_topic"#os.environ['sns_arn']

    # Build message
    message = 'Approve changes from Security Fairy here: {approval_url}'.format(approval_url=approval_url)


    sns_client.publish( TopicArn=sns_arn,
                        Message="{message}".format(message=message),
                        Subject='Security Fairy Permissions Request')

if __name__ == '__main__':
    event = {
                'execution_id':'8d544e31-37af-4eb2-acf3-b5eda9f108bd',
                'task-token': 'some-guid-i-get'
            }
    lambda_handler(event, {})
