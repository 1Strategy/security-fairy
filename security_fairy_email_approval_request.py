
import boto3
import json
import datetime

# Use the Boto3 SDK to create a client to call SNS functions



def lambda_handler(event, context):

    token = event.get(token)
    approval_url = 'https://.../' + token

    sns_client = boto3.client('sns', region_name='us-west-2')
    sns_arn = os.environ['sns_arn']

    # Build message
    message = 'Approve changes from Security Fairy here: {approval_url}'.format(approval_url=approval_url)


    sns_client.publish( TopicArn=sns_arn,
                        Message="{message}".format(message=message),
                        Subject='Security Fairy Permissions Request')
