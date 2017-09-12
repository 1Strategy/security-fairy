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
from tools import Arn
from tools import IAMPolicy


logging_level = logging.INFO
logging.basicConfig(level=logging_level)

try:
    SESSION = boto3.session.Session(profile_name='training', region_name='us-east-1')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


__author__ = 'Justin Iravani'


class NoResults(Exception):
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

    raw_query_results = get_query_results(query_execution_id)
    aws_entity = get_entity_arn_v2(raw_query_results)

    service_level_actions = get_permissions_from_query_v2(raw_query_results)

    new_iam_policy = IAMPolicy()
    new_iam_policy.add_actions(service_level_actions)

    logging.info(aws_entity.get_entity_name())
    existing_entity_policies = get_existing_entity_policies_v2(aws_entity.get_entity_name())
    write_policies_to_dynamodb(query_execution_id, new_iam_policy.print_policy(), aws_entity.get_full_arn(), event.get('dynamodb_table','security_fairy_dynamodb_table'))

    event['execution_id'] = query_execution_id

    return event


def get_query_results(query_execution_id):
    """Retrieve result set from Athena query"""

    athena_client = SESSION.client('athena')
    result_set = []
    query = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
    logging.debug(query)
    query_state = query['QueryExecution']['Status']['State']
    logging.debug(query_state)


    if query_state in ['FAILED', 'CANCELLED']:
        raise RuntimeError("Query failed to execute")

    if query_state in ['QUEUED', 'RUNNING']:
        raise Exception("Query still running")

    try:
        results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
        logging.debug(results)
        for result in results["ResultSet"]["Rows"][1:]:
            result_set.append(result["Data"])
        logging.debug(result_set)

    except ClientError as cle:
        logging.debug(cle)

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
    logging.debug('service actions from Athena Query')
    logging.debug(permissions)
    return permissions


def get_existing_entity_policies_v2(role_name):
    """
    Retrieve existing managed policies for the queried role
    """
    iam_client = SESSION.client('iam')
    logging.debug("role_name")
    logging.debug(role_name)
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
    dynamodb_client.put_item(TableName=dynamodb_table,
                             Item={
                                 "execution_id": {
                                     "S": execution_id
                                 },
                                 "new_policy":{
                                     "S": policy
                                 },
                                 "entity_arn": {
                                     "S": entity_arn
                                 }
                             }
                            )


def get_entity_arn_v2(result_set):
    entity_arn = result_set[0][0]['VarCharValue']
    logging.debug(entity_arn)
    arn = Arn(entity_arn)
    arn.convert_assumed_role_to_role()
    return arn


if __name__ == '__main__':

    lambda_handler(
        {
            "execution_id": "7b12e31a-b77d-4b30-9e13-0565fe465873"
        },
        {}
    )
