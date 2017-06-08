import boto3
import time
import re

try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()


def lambda_handler(event, context):
    token = event['token']
    delete_revised_policy(token)


def delete_revised_policy(token):
    session.client( 'dynamodb',
                    region_name = 'us-west-2') \
                    .delete_item(   TableName='security_fairy_pending_approval',
                                    Key={
                                        "token":{
                                            "S": token
                                        }
                                    })
