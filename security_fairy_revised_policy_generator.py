import boto3
import time
import json
import re
from botocore.exceptions import ClientError

__author__ = 'Justin Iravani'

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
    query_execution_id = 8d544e31-37af-4eb2-acf3-b5eda9f108bd
"""


def lambda_handler(event, context):
    query_execution_id = event.get('query_execution_id')

    if query_execution_id is None:
        raise ValueError("Lambda Function requires 'query_execution_id' to execute.")

    raw_query_results = get_query_results(query_execution_id)
    print(raw_query_results)

    entity_arn = get_entity_arn(raw_query_results)
    print(entity_arn)

    service_level_actions = get_permissions_from_query(raw_query_results)
    print(service_level_actions)

    query_action_policy = build_policy_from_query_actions(service_level_actions)
    print(query_action_policy)

    existing_entity_policies = get_existing_entity_policies(entity_arn)
    print(existing_entity_policies)

    write_policies_to_dynamodb(query_execution_id, query_action_policy, entity_arn)

    return {
        'execution_id': query_execution_id
    }

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
    permissions = {}

    for result in result_set:
        service = get_service_alias(result[1]['VarCharValue'].split('.')[0])
        actions = result[2]['VarCharValue'].strip('[').strip(']').split(', ')
        for action in actions:
            if permissions.get(service) is None:
                permissions[service]=[action]

            elif permissions.get(service) is not None:
                if action not in permissions[service]:
                    permissions[service].append(action)
    return permissions
    # {u'iam': [u'GetGroup'], u'lambda': [u'ListFunctions20150331', u'DeleteFunction20150331'], u'kms': [u'Decrypt'], u'ec2': [u'DescribeAddresses'], u'logs': [u'CreateLogStream', u'CreateLogGroup']}


def get_existing_entity_policies(entity_arn):
    iam_client = session.client('iam')
    policies = []

    # describe existing policies
    existing_policies = iam_client.list_attached_role_policies(RoleName=re.split('/|:', entity_arn)[5])['AttachedPolicies']
    for existing_policy in existing_policies:
        if 'arn:aws:iam::aws:policy' not in existing_policy['PolicyArn']:
            print(existing_policy)
    return policies


def build_policy_from_query_actions(service_level_actions):

    built_policies = []

    built_policy = {
        "Version": "2012-10-17",
        "Statement": []
    }

    for key, value in service_level_actions.items():

        api_permissions = []

        for item in value:
            api_permissions.append("{}:{}".format(key,item).encode('ascii', 'ignore'))

        built_policy['Statement'].append(
                {
                    "Sid": "SecurityFairyBuiltPolicy{key}".format(key=key.capitalize()),
                    "Action": api_permissions,
                    "Effect": "Allow",
                    "Resource": "*"
                }
        )
    return json.dumps(built_policy)

def write_policies_to_dynamodb(execution_id, policies, entity_arn):

    # dynamodb_table = event['dynamodb_table']

    dynamodb_client = session.client('dynamodb', region_name='us-west-2')
    dynamodb_client.put_item(TableName='security_fairy_pending_approval',
                             Item={
                                "execution_id":{
                                    "S": execution_id
                                },
                                "new_policy":{
                                    "S": policies
                                },
                                "entity_arn":
                                {
                                    "S":entity_arn
                                }
                             })

def get_service_alias(service):
    service_aliases = {
        "monitoring": "cloudwatch"
    }
    return service_aliases.get(service, service)

def get_entity_arn(result_set):
    try:
        entity_arn = result_set[0][0]['VarCharValue']
        print(entity_arn)
        split_arn = re.split('/|:', entity_arn)
        print(split_arn)
        return "arn:aws:iam:" + split_arn[4] + ":role/" + split_arn[6]
    except IndexError as ie:
        print(ie)
        raise ValueError('The Athena query didn\'t return any results.')
    except Exception as e:
        print(e)
        raise Exception(e)

if __name__ == '__main__':
    lambda_handler({
        'query_execution_id': '8d544e31-37af-4eb2-acf3-b5eda9f108bd'
    },{})
