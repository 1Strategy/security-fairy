import boto3
import json
import logging
import os
import re
from tools import Arn
from botocore.exceptions import ProfileNotFound
from boto3.dynamodb.conditions import Key


try:
    SESSION = boto3.session.Session(profile_name='training',
                                    region_name='us-east-1')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


def lambda_handler(event, context):

    method      = event['httpMethod']

    if method == 'GET':
        pass
    if method == 'POST':
        entity_to_revert  = json.loads(event['body'].get('entity_arn', {}))
        entity_arn = Arn(entity_to_revert).get_full_arn()
        post_response(entity_arn)

    api_return_payload = {
        'statusCode': 405,
        'headers':{
            'Content-Type':'text/html'
        },
        'body':'Security Fairy Error - HTTP Method or Input not supported.'
    }

    return api_return_payload

def get_response():
    return {
        'statusCode': 500,
        'headers':{
            'Content-Type':'text/html'
        },
        'body':'Security Fairy Error - Get method is fubar'
    }


def post_response(entity_arn):
    try:
        revert_role_managed_policies(entity_arn)
    except Exception:
        return {
                    'statusCode': 405,
                    'headers':{
                    'Content-Type':'text/html'
                    },
                    'body':'Security Fairy Error - Role wasn\'t reverted properly.'
                }


def revert_role_managed_policies(role_arn):
    """
    Reverts role to pre-security fairy permissions
    """
    associate_preexisting_policies(role_arn)
    disassociate_security_fairy_policy(role_arn)


def associate_preexisting_policies(entity_arn):
    iam_client      = SESSION.client('iam')
    dynamodb_client = SESSION.client('dynamodb')
    # reach out to security_fairy_dynamodb_table and get 'existing_policies' field

    response_item   = dynamodb_client.query(
                          TableName='security_fairy_revised_policy',#os.environ['dynamodb_table'],
                          IndexName='entity_arn',
                          Select='ALL_ATTRIBUTES',
                          KeyConditionExpression=Key("entity_arn").eq(entity_arn)
                      )['Items']
    logging.debug(response_item)

    # for each item in 'existing_policies' attach policy to 'role_arn'
    # for policy in existing_policies:
    #     attachment_response = iam_client.attach_role_policy(RoleName=entity_arn,
    #                                                         PolicyArn=policy
    #                                                         )


def disassociate_security_fairy_policy(entity_arn):
    iam_client      = SESSION.client('iam')
    arn = Arn(entity_arn)
    account_number  = arn.get_account_number()
    entity_name     = arn.get_entity_name()

    policy_arn      =  'arn:aws:iam::{account_number}:policy/security-fairy/{entity_name}-security-fairy-revised-policy'\
                            .format(account_number=account_number,
                                    entity_name=entity_name
                                    ).replace('_','-')
    logging.debug(policy_arn)

    detach_policy(entity_name, policy_arn)
    delete_policy(policy_arn)


def detach_policy(entity_name, policy_arn):
    try:
        iam_client.detach_role_policy(RoleName=entity_name, PolicyArn=policy_arn)
    except Exception as error:
        loggin.debug(error)


def delete_policy(policy_arn):

    iam_client      = SESSION.client('iam')
    policy_versions = iam_client.list_policy_versions( PolicyArn=policy_arn)['Versions']

    for version in policy_versions:
        if not version['IsDefaultVersion']:
            iam_client.delete_policy_version(   PolicyArn=policy_arn,
                                                VersionId=version['VersionId'])
    iam_client.delete_policy(PolicyArn=policy_arn)


if __name__ == '__main__':
    # entity_arn = 'arn:aws:iam::281782457076:role/1s_tear_down_role'
    # disassociate_security_fairy_policy(entity_arn)
    # delete_policy('arn:aws:iam::281782457076:policy/security-fairy/1s-tear-down-role-security-fairy-revised-policy')
    associate_preexisting_policies("arn:aws:iam::281782457076:role/1s_tear_down_role")
