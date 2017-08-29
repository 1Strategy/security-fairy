"""Revised Policy Generator

Builds a revised policy for the queried
role using data retrieved from Athena.
"""

from __future__ import print_function
import json
import re
import boto3
import logging
from botocore.exceptions import ClientError
from botocore.exceptions import ProfileNotFound


try:
    SESSION = boto3.session.Session(profile_name='training', region_name='us-east-1')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


__author__ = 'Justin Iravani'


class NoResults(Exception):
    """No Results Class"""
    pass


def lambda_handler(event, context):
    """ Executed by the Lambda service.

    Returns a revised policy after retrieving
    the results of the Security Fairy Athena query.
    """

    query_execution_id = event.get('execution_id')

    if query_execution_id is None:
        raise ValueError("Lambda Function requires 'query_execution_id' to execute.")

    raw_query_results     = get_query_results(query_execution_id)
    entity_arn            = get_entity_arn(raw_query_results)
    service_level_actions = get_permissions_from_query(raw_query_results)
    query_action_policy   = build_policy_from_query_actions(service_level_actions)
    # existing_entity_policies = get_existing_entity_policies(entity_arn)
    write_policies_to_dynamodb(query_execution_id, query_action_policy, entity_arn, event.get('dynamodb_table','security_fairy_dynamodb_table'))
    event['execution_id'] = query_execution_id

    return event


def get_query_results(query_execution_id):
    """Retrieve result set from Athena query"""

    athena_client = SESSION.client('athena')
    result_set = []
    query_state = athena_client.get_query_execution(QueryExecutionId=query_execution_id)['QueryExecution']['Status']['State']
    print(query_state['QueryExecution']['Status']['State'])

    if query_state in ['FAILED', 'CANCELLED']:
        raise RuntimeError("Query failed to execute")

    if query_state in ['QUEUED', 'RUNNING']:
        raise Exception("Query still running")

    try:
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        print(results)
        for result in results["ResultSet"]["Rows"][1:]:
            result_set.append(result["Data"])
        print(result_set)

    except ClientError as cle:
        print(cle)

    if not result_set:
        raise NoResults("Athena ResultSet {result_set}".format(result_set=result_set))

    return result_set


def get_permissions_from_query(result_set):
    """Retrieve permissions from Athena query results"""

    permissions = {}

    for result in result_set:
        service = get_service_alias(result[1]['VarCharValue'].split('.')[0])
        actions = result[2]['VarCharValue'].strip('[').strip(']').split(', ')
        for action in actions:
            if permissions.get(service) is None:
                permissions[service] = [action]

            elif permissions.get(service) is not None:
                if action not in permissions[service]:
                    permissions[service].append(action)
    return permissions
    # {u'iam': [u'GetGroup'], u'lambda': [u'ListFunctions20150331', u'DeleteFunction20150331'], u'kms': [u'Decrypt'], u'ec2': [u'DescribeAddresses'], u'logs': [u'CreateLogStream', u'CreateLogGroup']}

def refactored_get_permissions_from_query(result_set):

    permissions = {}

    for result in result_set:
        service = get_service_alias(result[1]['VarCharValue'].split('.')[0])
        actions = result[2]['VarCharValue'].strip('[').strip(']').split(', ')
        compiled_actions = compile_actions(service, actions)
        permissions.update(compiled_actions)

    return permissions


def compile_actions(service, actions):
    """ This is a stub for a sub function of get_permissions_from_query(result_set)
        specifically with the intention of handling lambda permissions with give
        legacy names for the API calls in CloudTrail e.g. ListFunctions20150331 vs ListFunctions
        Which causes access denieds in a new policy
    """
    permissions = {}
    for action in actions:

        if service == 'lambda':
            pattern = re.compile(r'^([a-zA-z]*)(20).*')
            if pattern.match(action):
                action = action.split('20')[0]
                print(action)

        if permissions.get(service) is None:
            permissions[service]=[action]

        elif permissions.get(service) is not None:
            if action not in permissions[service]:
                permissions[service].append(action)

    return permissions


def get_existing_entity_policies(entity_arn):
    """Retrieve existing managed policies for
    the queried role
    """
    iam_client = SESSION.client('iam')
    policies = []

    # describe existing policies
    role_name = re.split('/|:', entity_arn)[5]
    attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
    existing_policies = attached_policies['AttachedPolicies']
    for existing_policy in existing_policies:
        if 'arn:aws:iam::aws:policy' not in existing_policy['PolicyArn']:
            print(existing_policy)
    return policies


def build_policy_from_query_actions(service_level_actions):
    """Build revised policy"""

    # built_policies = []
    # policy_num = 0
    built_policy = {
        "Version": "2012-10-17",
        "Statement": []
    }

    for key, value in service_level_actions.items():

        api_permissions = []

        for item in value:
            item_dict = "{key}:{item}"\
                        .format(key=key, item=item)\
                            .encode('ascii', 'ignore')

            api_permissions.append(item_dict)


        built_policy['Statement'].append(
            {
                "Sid": "SecurityFairyBuiltPolicy{key}".format(key=key.capitalize()),
                "Action": api_permissions,
                "Effect": "Allow",
                "Resource": "*"
            })

        # if len(json.dumps(built_policy['Statement'])) > MAX_POLICY_SIZE['role'] - 1000:
        #     print(len(json.dumps(built_policy['Statement'])))
        #     policy_num += 1;

    return json.dumps(built_policy)


def write_policies_to_dynamodb(execution_id, policies, entity_arn, dynamodb_table):
    """Write policies to DynamoDB table"""

    dynamodb_client = SESSION.client('dynamodb')
    dynamodb_client.put_item(TableName=dynamodb_table,
                             Item={
                                 "execution_id": {
                                     "S": execution_id
                                 },
                                 "new_policy":{
                                     "S": policies
                                 },
                                 "entity_arn": {
                                     "S": entity_arn
                                 }
                             }
                            )


def get_service_alias(service):
    """Extract service aliases"""

    service_aliases = {
        "monitoring": "cloudwatch"
    }
    return service_aliases.get(service, service)


def get_entity_arn(result_set):
    """Extract entity ARN"""

    entity_arn = result_set[0][0]['VarCharValue']
    print(entity_arn)
    split_arn = re.split('/|:', entity_arn)
    print(split_arn)
    return "arn:aws:iam:" + split_arn[4] + ":role/" + split_arn[6]


if __name__ == '__main__':

    lambda_handler(
        {
            "execution_id": "3f4c49d2-465d-4c6a-8e97-ba0ddfd6fc1c"
        },
        {}
    )
