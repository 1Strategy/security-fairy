"""Revised Policy Approve

Implements the changes suggested by Security
Fairy. Detaches the existing policy for the
queried role and attaches the revised policy.
"""


import boto3
import os
import logging
import re
from setup_logger import create_logger
from tools import Arn
from botocore.exceptions import ProfileNotFound

try:
    SESSION = boto3.session.Session(profile_name='training', region_name='us-east-1')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


logger = create_logger(name='revised_policy_approve.py', logging_level=logging.INFO)


def lambda_handler(event, context):
    """ Executed by the Lambda service.

    Detaches the existing managed policies from the
    queried role and attaches the Security Fairy
    revised policy.
    """
    try:
        execution_id    = event['execution_id']
        logger.debug(execution_id)
        dynamodb_table  = event.get('dynamodb_table', os.environ['dynamodb_table'])
        logger.debug(dynamodb_table)

        policy_object   = get_revised_policy(execution_id, dynamodb_table)
        logger.debug(policy_object)
        entity_name     = Arn(policy_object['entity_arn']).get_entity_name()
        logger.debug(entity_name)

        existing_policies = get_existing_managed_policies(entity_name)
        preserve_existing_policies(execution_id, existing_policies, dynamodb_table)
        apply_revised_policy(policy_object)
        detach_existing_policies(entity_name, existing_policies)


    except Exception as error:
        logger.info("There was an error: ")
        logger.info(error)

def apply_revised_policy(policy_object):
    """Attach Security Fairy's suggested policy"""

    iam_client = SESSION.client('iam')

    entity_arn      = Arn(policy_object['entity_arn'])
    policy          = policy_object['policy']
    entity_name     = entity_arn.get_entity_name()
    account_number  = entity_arn.get_account_number()
    policy_name     = "{entity_name}-security-fairy-revised-policy"\
                        .format(entity_name=entity_name) \
                            .replace("_","-")

    logger.info("Attaching: ")
    logger.info(policy_name)

    try:
        new_policy_arn = create_new_policy(policy_name, policy)
    except Exception as e:
        logger.info(e)
        new_policy_arn = create_new_policy_version(policy_name, policy, account_number)

    logger.debug(new_policy_arn)

    attachment_response = iam_client.attach_role_policy(RoleName=entity_name,
                                                        PolicyArn=new_policy_arn)
    logger.debug(attachment_response)


def create_new_policy(policy_name, policy):
    iam_client          = SESSION.client('iam')
    creation_response   = iam_client.create_policy( PolicyName=policy_name,
                                                    Path='/security-fairy/',
                                                    PolicyDocument=policy,
                                                    Description='This is an autogenerated policy from Security Fairy')
    logger.debug(creation_response)
    created_policy_arn = creation_response['Policy']['Arn']
    return created_policy_arn


def create_new_policy_version(policy_name, policy, account_number):

    policy_arn = "arn:aws:iam::{account_number}:policy/security-fairy/{policy_name}" \
                    .format(account_number=account_number, policy_name=policy_name)

    iam_client  = SESSION.client('iam')

    versions    = iam_client.list_policy_versions( PolicyArn=policy_arn)['Versions']
    logger.debug(versions)
    if len(versions) > 1:
        version_id = versions[1]['VersionId']
        logger.debug(version_id)
        iam_client.delete_policy_version(   PolicyArn=policy_arn,
                                            VersionId=version_id)
    # apply new version
    response = iam_client.create_policy_version(PolicyArn=policy_arn,
                                                PolicyDocument=policy,
                                                SetAsDefault=True)
    logger.info("Policy version {} created.".format(response['PolicyVersion']['VersionId']))
    return policy_arn

def get_existing_managed_policies(entity_name):

    attached_policies = SESSION.client('iam').list_attached_role_policies(RoleName=entity_name)['AttachedPolicies']
    existing_policies = []
    for policy in attached_policies:
        logger.debug(policy['PolicyArn'])
        existing_policies.append(policy['PolicyArn'])

    logger.debug(existing_policies)
    return existing_policies


def preserve_existing_policies(execution_id, existing_policies, dynamodb_table):
    logger.debug(execution_id)
    logger.debug(existing_policies)
    logger.debug(dynamodb_table)

    dynamodb_client = SESSION.client('dynamodb')

    if not existing_policies:
        logger.info("There were no existing policies attached to this role.")
        return

    dynamodb_client.update_item(TableName=dynamodb_table,
                                Key={ "execution_id": { "S": execution_id }},
                                AttributeUpdates={
                                    "existing_policies": {
                                        "Value":{"SS": existing_policies}
                                    }})


def detach_existing_policies(entity_name, existing_policies):
    """Take existing managed IAM policies and remove them from the role"""
    logger.info("Detaching Policies: ")
    logger.info(existing_policies)
    for policy in existing_policies:
        logger.debug(policy)
        SESSION.client('iam').detach_role_policy(  RoleName=entity_name,
                                                   PolicyArn=policy)


def get_revised_policy(execution_id, dynamodb_table):
    """Retrieve Security Fairy's suggested policy"""
    return_response = {}
    try:
        dynamodb_response = SESSION.client('dynamodb')\
                                    .get_item( TableName=dynamodb_table,
                                               Key={
                                                "execution_id": {
                                                    "S": execution_id
                                                }
                                            })
        return_response['policy']       = dynamodb_response['Item']['new_policy']['S']
        return_response['entity_arn']   = dynamodb_response['Item']['entity_arn']['S']
        logger.debug(return_response)
        return return_response

    except Exception as e:
        logger.info(e)
        raise ValueError('Execution Id doesn\'t exist or has expired. \
                          Security-fairy must be rerun.')




if __name__ == '__main__':
    # existing_policies   = ['arn:aws:iam::aws:policy/AmazonS3FullAccess', 'arn:aws:iam::281782457076:policy/security-fairy/1s-security-fairy-role-security-fairy-revised-policy', 'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess', 'arn:aws:iam::aws:policy/AdministratorAccess']
    # dynamodb_table      = 'security_fairy_dynamodb_table'
    # execution_id        = '830eb4f7-364f-44b2-8617-578276ce2270'
    # preserve_existing_policies(execution_id, existing_policies, dynamodb_table)

    lambda_handler({
                        "execution_id": "869f474a-d594-42be-869c-3362c063f940",
                        "dynamodb_table": "security_fairy_dynamodb_table"
                    }
                    , {})
    # existing_policies = ['arn:aws:iam::aws:policy/AmazonS3FullAccess', 'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess', 'arn:aws:iam::aws:policy/AdministratorAccess']
    # dynamodb_table = 'security_fairy_dynamodb_table'
    # execution_id = '4bb5d1ad-17ed-43d7-a06b-59ead4a9cf00'
    # preserve_existing_policies(execution_id, existing_policies, dynamodb_table)
    # print(get_existing_managed_policies('1s_security_fairy_role'))
