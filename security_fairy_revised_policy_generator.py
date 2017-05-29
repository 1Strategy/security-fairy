import boto3
import time
import json
from botocore.exceptions import ClientError

# Create AWS session
try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()

max_policy_size = {
    'user':2048,    # User policy size cannot exceed 2,048 characters
    'role':10240,   # Role policy size cannot exceed 10,240 characters
    'group':5120    # Group policy size cannot exceed 5,120 characters
}


# Connect to Athena

# Requested

# Get existing

# Email token

"""
for testing Athena Query Id:
    query_execution_id = 52e009f3-5a3a-4226-b562-dc9316a2995d
"""


def lambda_handler(event, context):
    query_execution_id = event.get('query_execution_id')

    if query_execution_id is None:
        raise ValueError("Lambda Function requires 'query_execution_id' to execute.")

# Get Query Results
    raw_query_results = get_query_results(query_execution_id)
    print(raw_query_results)
# Get entity_arn
    entity_arn = get_entity_arn(raw_query_results)
    print(entity_arn)
# Get api level permissions from query
    service_level_actions = get_permissions_from_query(raw_query_results)
    print(service_level_actions)

# Build new Policy
    query_action_policy = build_policy_from_query_actions(service_level_actions)
    print(query_action_policy)
# Get Existing policies
    # existing_entity_policies = get_existing_entity_policies(entity_arn)
# Create New Policy
# Generate a diff
# Push to DynamoDB

<<<<<<< HEAD
    return {
        'query_execution_id': query_execution_id
    }
=======
>>>>>>> 8595af339c53aa2226fa9b4c90f70579f85b8f33

def get_query_results(query_execution_id):

    athena_client = session.client('athena', region_name='us-east-1')
    result_set = []

    try:
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        print(results)
        for result in results["ResultSet"]["Rows"][1:]:
            result_set.append(result["Data"])

    except ClientError as e:
        print(e)

    return result_set


def get_permissions_from_query(result_set):
    permissions = []
    for result in result_set:
        permissions.append(get_service_level_actions(result))
    return permissions


def get_existing_entity_policies(entity_arn):
    iam_client = session.client('iam')
    policies = []
    # describe existing policies
    policies = iam_client.list_attached_role_policies(RoleName=entity_arn)
    print(policies)
    return policies

def build_revised_policy(entity_arn):
    iam_client = session.client('iam')


def build_policy_from_query_actions(service_level_actions):
    built_policy = {
        "Version": "2012-10-17",
        "Statement": []
    }
    for actions in service_level_actions:
        built_policy['Statement'].append(
                {
                    "Sid": "SecurityFairyBuiltPolicy{service}".format(service=actions[0].split(':')[0].capitalize()),
                    "Action": actions,
                    "Effect": "Allow",
                    "Resource": "*"
                }
            )

    print(len(json.dumps(built_policy)))
    return json.dumps(built_policy)


def write_policies_to_dynamodb(policies):

    dynamodb_table = event['dynamodb_table']

    dynamodb_client = boto3.client('dynamodb', region_name='us-west-2')
    dynamodb_client.put_item(TableName='security_fairy_pending_approval',
                             Item={})

def get_service_level_actions(result):

    entity_arn = result[0]['VarCharValue']
    service = get_service_alias(result[1]['VarCharValue'].split('.')[0])
    actions = result[2]['VarCharValue'].strip('[').strip(']').split(', ')

    all_actions = []

    for action in actions:
        api_permission = service+':'+ action
        all_actions.append(api_permission)
    return all_actions

def get_service_alias(service):
    service_aliases = {
        'monitoring': 'cloudwatch'
    }

    return service_aliases.get(service, service)

def get_entity_arn(result_set):
    try:
        return result_set[0][0]['VarCharValue']
    except IndexError as ie:
        raise ValueError('The Athena query didn\'t return any results'.)
    except Exception as e:
        raise Exception(e)

if __name__ == '__main__':
    lambda_handler({
<<<<<<< HEAD
        'query_execution_id': '5f57f83c-69a7-4a53-870e-5b9639795906'
    },{})
=======
        'query_execution_id': '52e009f3-5a3a-4226-b562-dc9316a2995d'
    }, {})
>>>>>>> 8595af339c53aa2226fa9b4c90f70579f85b8f33
