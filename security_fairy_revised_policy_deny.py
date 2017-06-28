"""Revised Policy Deny

Discards the changes suggested by
Security Fairy.
"""


import json
import os
import boto3
from botocore.exceptions import ProfileNotFound


try:
    SESSION = boto3.session.Session(profile_name='training')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


def lambda_handler(event, context):
    """ Executed by the Lambda service.

    Deletes Security Fairy's suggested
    policy from the DynamoDB table.
    """

    print event
    event = json.loads(event['Cause'])
    print event
    execution_id = event['execution_id']
    dynamodb_table = os.environ['dynamodb_table']

    delete_revised_policy(dynamodb_table, execution_id)


def delete_revised_policy(dynamodb_table, execution_id):
    """Delete Security Fairy's suggested policy"""

    SESSION.client('dynamodb')\
                    .delete_item(TableName=dynamodb_table,
                                 Key={
                                     "execution_id":{
                                         "S": execution_id
                                         }
                                     }
                                )


if __name__ == '__main__':
    lambda_handler(
        {}, {}
    )
