import boto3
import json
import logging
import os
import re
from botocore.exceptions import ProfileNotFound

logging.debug('This message should go to the log file')
logging.info('So should this')


try:
    SESSION = boto3.session.Session(profile_name='training',
                                    region_name='us-east-1')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()

def lambda_handler(event, context):
    pass
    # get
    # post_response

def get_response():
    pass


def post_response():
    pass


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

    #TODO ask alex
    # response_item   = dynamodb_client.get_item( TableName='security_fairy_revised_policy'#os.environ['dynamodb_table'],
    #                                             Key={
    #                                                 "entity_arn": {
    #                                                     "S": "{entity_arn}".format(entity_arn=entity_arn)
    #                                                 }
    #                                             })['Item']
    # print(response_item)

    # for each item in 'existing_policies' attach policy to 'role_arn'
    # for policy in existing_policies:        
    #   attachment_response = iam_client.attach_role_policy(RoleName=entity_arn,
    #                                                       PolicyArn=policy)

def disassociate_security_fairy_policy(entity_arn):

    iam_client = SESSION.client('iam')

    split_arn       = re.split('/|:', entity_arn)
    account_number  = split_arn[4]
    entity_name     = split_arn[6]

    policy_arn      =  'arn:aws:iam::{account_number}:policy/security-fairy/{entity_name}_security_fairy_revised_policy'\
                            .format(account_number=account_number,
                                    entity_name=entity_name
                                    ).replace('_','-')
    print(policy_arn)

    detach_policy(entity_name, policy_arn)
    delete_policy(policy_arn)


def detach_policy(entity_name, policy_arn):
    try:
        iam_client.detach_role_policy(RoleName=entity_name, PolicyArn=policy_arn)
    except Exception as error:
        print(error)


def delete_policy(policy_arn):

    iam_client      = SESSION.client('iam')
    policy_versions = iam_client.list_policy_versions( PolicyArn=policy_arn)['Versions']

    for version in policy_versions:
        if not version['IsDefaultVersion']:
            iam_client.delete_policy_version(   PolicyArn=policy_arn,
                                                VersionId=version['VersionId'])
    iam_client.delete_policy(PolicyArn=policy_arn)


if __name__ == '__main__':
    entity_arn = 'arn:aws:iam::281782457076:role/1s_tear_down_role'
    # disassociate_security_fairy_policy(entity_arn)
    delete_policy('arn:aws:iam::281782457076:policy/security-fairy/1s-tear-down-role-security-fairy-revised-policy')
