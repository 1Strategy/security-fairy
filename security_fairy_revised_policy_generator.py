import boto3
import time
from botocore.exceptions import ClientError

# Create AWS session
try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()

# Connect to Athena

# Requested permissions

# Get existing permissions

# DynamoToken (QueryId)

# Pass token

#for testing Athena Query Id:
# query_execution_id = 52e009f3-5a3a-4226-b562-dc9316a2995d

def lambda_handler(event, context):
    query_execution_id = event.get('query_execution_id')

    if query_execution_id is None:
        raise ValueError("Lambda Function requires 'query_execution_id' to execute.")

# Get Query Results
    raw_query_result = get_query_results(query_execution_id)
# Get Existing policies
# Create New Policy
# Generate a diff
# Push to DynamoDB

def get_query_results(query_execution_id):

    athena_client = session.client('athena', region_name = 'us-east-1')
    result_set = []

    try:
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        for result in results["ResultSet"]["Rows"][1:]:
            result_set.append(result["Data"])

    except ClientError as e:
        raise(e)

    print(result_set)
    return result_set


def get_permissions_from_query(results):
    pass


def build_revised_policy(entity_arn):
    iam_client = session.client('iam')


def write_policies_to_dynamodb(, context):

    dynamodb_table = event['dynamodb_table']

    dynamodb_client = boto3.client('dynamodb', region_name='us-west-2')
    dynamodb_client.put_item(TableName='security_fairy_pending_approval',
                             Item={})


if __name__ == '__main__':
    lambda_handler({
        'query_execution_id': '52e009f3-5a3a-4226-b562-dc9316a2995d'
    },{})
