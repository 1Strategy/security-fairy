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
from setup_logger   import create_logger
from aws_entity     import AWSEntity
from aws_iam_policy import IAMPolicy

logger = create_logger(name="revised_policy_generator.py")

try:
    SESSION = boto3.session.Session(profile_name='training', region_name='us-east-1')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


__author__ = 'Justin Iravani'


class NoResults(Exception):
    """No Results Exception Class"""
    pass

class QueryFailed(Exception):
    """No Results Exception Class"""
    pass

class QueryStillRunning(Exception):
    """No Results Exception Class"""
    pass

def lambda_handler(event, context):
    """ Executed by the Lambda service.

    Returns a revised policy after retrieving
    the results of the Security Fairy Athena query.
    """

    query_execution_id = event.get('execution_id')

    if query_execution_id is None:
        raise ValueError("Lambda Function requires 'query_execution_id' to execute.")

    try:
        raw_query_results = get_query_results(query_execution_id)
        aws_entity = get_entity_arn(raw_query_results)
        event['query_state'] = 'QueryCompletedOrFailed'
    except QueryStillRunning as qsr:
        event['query_state'] = 'StillRunning'
        return event

    service_level_actions = get_permissions_from_query_v2(raw_query_results)

    new_iam_policy = IAMPolicy()
    new_iam_policy.add_actions(service_level_actions)

    logger.info(aws_entity.get_entity_name())
    existing_entity_policies = get_existing_entity_policies_v2(aws_entity.get_entity_name())
    write_policies_to_dynamodb(query_execution_id, new_iam_policy.print_policy(), aws_entity.get_full_arn(), event.get('dynamodb_table','security_fairy_dynamodb_table'))

    event['execution_id'] = query_execution_id

    return event


def get_query_results(query_execution_id):
    """Retrieve result set from Athena query"""

    athena_client = SESSION.client('athena')
    result_set = []
    query = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
    logger.debug(query)
    query_state = query['QueryExecution']['Status']['State']
    logger.debug(query_state)


    if query_state in ['FAILED', 'CANCELLED']:
        raise QueryFailed("Query failed to execute")

    if query_state in ['QUEUED', 'RUNNING']:
        raise QueryStillRunning("Query still running")

    try:
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        logger.debug(results)
        for result in results["ResultSet"]["Rows"][1:]:
            result_set.append(result["Data"])
        logger.debug(result_set)

    except ClientError as cle:
        logger.debug(cle)

    if not result_set:
        raise NoResults("Athena ResultSet {result_set}".format(result_set=result_set))

    return result_set


def get_permissions_from_query_v2(result_set):
    """
    Retrieve permissions from Athena query results
    v2
    """

    permissions = []

    for result in result_set:
        service = result[1]['VarCharValue'].split('.')[0]
        actions = result[2]['VarCharValue'].strip('[').strip(']').split(', ')
        for action in actions:
            permissions.append('{service}:{action}'.format(service=service, action=action))
    logger.debug('service actions from Athena Query')
    logger.debug(permissions)
    return permissions


def get_existing_entity_policies_v2(role_name):
    """
    Retrieve existing managed policies for the queried role
    """
    iam_client = SESSION.client('iam')
    logger.debug("role_name: {}".format(role_name))

    policies          = []
    attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
    existing_policies = attached_policies['AttachedPolicies']
    for existing_policy in existing_policies:
        if 'arn:aws:iam::aws:policy' not in existing_policy['PolicyArn']:
            print(existing_policy)

    return existing_policies


def write_policies_to_dynamodb(execution_id, policy, entity_arn, dynamodb_table):
    """Write policies to DynamoDB table"""
    dynamodb_client = SESSION.client('dynamodb')
    dynamodb_item_to_be_written = {}
    existing_item = existing_dynamodb_entry(entity_arn, dynamodb_table)

    if existing_item:
        dynamodb_item_to_be_written = existing_item[0]
        existing_execution_id = dynamodb_item_to_be_written['execution_id']['S']
        delete_execution(existing_execution_id, dynamodb_table)
        dynamodb_item_to_be_written['new_policy']   = { "S": policy }
        dynamodb_item_to_be_written['execution_id'] = { "S": execution_id }
    else:
        dynamodb_item_to_be_written = { "execution_id": { "S": execution_id },
                                        "new_policy"  : { "S": policy       },
                                        "entity_arn"  : { "S": entity_arn   }}
    logger.debug("Updated dynamodb_item: {}".format(dynamodb_item_to_be_written))
    dynamodb_client.put_item(TableName=dynamodb_table,
                             Item=dynamodb_item_to_be_written)


def existing_dynamodb_entry(entity_arn, dynamodb_table):
    dynamodb_client = SESSION.client('dynamodb')
    response = dynamodb_client.scan(TableName=dynamodb_table,
                                    # IndexName='entity_arn',
                                    ScanFilter={ 'entity_arn': {'AttributeValueList': [{ 'S': entity_arn }],
                                                                'ComparisonOperator': 'EQ'}})
    return response.get('Items')


def delete_execution(execution_id, dynamodb_table):
    dynamodb_client = SESSION.client('dynamodb')
    response = dynamodb_client.delete_item( TableName=dynamodb_table,
                                            Key={ 'execution_id': { 'S': execution_id }})


def get_entity_arn(result_set):
    entity_arn = result_set[0][0]['VarCharValue']
    logger.debug(entity_arn)
    arn = AWSEntity(entity_arn)
    arn.convert_assumed_role_to_role()
    return arn


if __name__ == '__main__':
    existing_execution_id_for_role('arn:aws:iam::281782457076:role/1s_tear_down_role')
    # lambda_handler(
    #     {
    #         "execution_id": "ed3dda30-b1d0-4191-ab88-ce2718b89485"
    #     },
    #     {}
    # )
