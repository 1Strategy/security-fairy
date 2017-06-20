import boto3
import json
import os

try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()


def lambda_handler(event, context):
    print(event)
    event           = json.loads(event['Cause'])
    print(event)
    execution_id    = event['execution_id']
    dynamodb_table  = os.environ['dynamodb_table']

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
    lambda_handler(
        {

    },{})
