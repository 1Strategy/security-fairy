import boto3
import time
import re

try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()


def lambda_handler(event, context):
    execution_id = event['execution_id']
    delete_revised_policy(execution_id)


def delete_revised_policy(execution_id):
    session.client( 'dynamodb',
                    region_name = 'us-west-2') \
                    .delete_item(   TableName='security_fairy_pending_approval',
                                    Key={
                                        "execution_id":{
                                            "S": execution_id
                                        }
                                    })
