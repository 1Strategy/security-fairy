import boto3
import time
import re

try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()


def lambda_handler(event, context):

    execution_id    = event['execution_id']
    dynamodb_table  = event['dynamodb_table']
    delete_revised_policy(dynamodb_table, execution_id)


def delete_revised_policy(dynamodb_table, execution_id):
    session.client( 'dynamodb') \
                    .delete_item(   TableName=dynamodb_table,
                                    Key={
                                        "execution_id":{
                                            "S": execution_id
                                        }
                                    })
if __name__ == '__main__':
    lambda_handler({
        'execution_id':'xyz-8d544e31-37af-4eb2-acf3-b5eda9f108bd'
    },{})
