import boto3
import json
import logging
import os
import re
from tools import Arn
from setup_logger import create_logger
from botocore.exceptions import ProfileNotFound
from boto3.dynamodb.conditions import Key

logger = create_logger(name = __name__, logging_level=logging.INFO)

try:
    SESSION = boto3.session.Session(profile_name='training',
                                    region_name='us-east-1')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


def lambda_handler(event, context):

    method = event['httpMethod']

    if method == 'GET':
        logger.info('Request was an HTTP GET Request')
        return get_response()

    if method == 'POST':
        logger.info('Request was an HTTP POST Request')
        posted_arn = json.loads(event['body'])['entity_arn']
        logger.info('Body: {}'.format(posted_arn))
        entity_arn = Arn(posted_arn)
        return post_response(entity_arn)

    return api_response()


def get_response():
    return api_response(body='GET Method failed.')


def get_all_iam_audited_entities():

    dynamodb_client = SESSION.client('dynamodb')
    response_item = dynamodb_client.scan(
                        TableName='security_fairy_dynamodb_table',
                        AttributesToGet=[
                            'entity_arn',
                            'existing_policies'
                        ])['Items']
    logger.info(response_item)
    return response_item


def post_response(entity_arn):
    try:
        revert_role_managed_policies(entity_arn)
    except Exception as e:
        # Generic "catch-all exception"
        logger.info(e)
        return api_response(body='Error - Role wasn\'t reverted properly.')

    return api_response(statusCode=200, body='Success: The IAM Role has had it\'s pre-security fairy permissions established')


def revert_role_managed_policies(role_arn):
    """
    Reverts role to pre-security fairy permissions
    """
    associate_preexisting_policies(role_arn)
    disassociate_security_fairy_policy(role_arn)


def get_preexisting_policies(entity_arn):

    dynamodb_client = SESSION.client('dynamodb')

    # reach out to security_fairy_dynamodb_table and get 'existing_policies' field
    response_item = dynamodb_client.scan(
                        TableName='security_fairy_dynamodb_table',
                        IndexName='entity_arn',
                        AttributesToGet=
                        [
                            'execution_id',
                            'entity_arn',
                            'existing_policies'
                        ],
                        ScanFilter={
                            'entity_arn': {
                                'AttributeValueList': [
                                    {
                                        'S': entity_arn
                                    }
                                ],
                                'ComparisonOperator': 'EQ'
                            }
                        }
                        )['Items'][0]

    logger.info(response_item)
    existing_policies = response_item['existing_policies']['SS']
    logger.info(existing_policies)

    return existing_policies


def associate_preexisting_policies(entity_arn):

    iam_client = SESSION.client('iam')

    validated_entity = Arn(entity_arn)
    existing_policies = get_preexisting_policies(entity_arn)
    role_name = validated_entity.get_entity_name()

    # for each item in 'existing_policies' attach policy to 'role_arn'
    for policy in existing_policies:
        logger.info(policy)
        attachment_response = iam_client.attach_role_policy(RoleName=role_name,
                                                            PolicyArn=policy)


def disassociate_security_fairy_policy(entity_arn):
    iam_client      = SESSION.client('iam')
    arn = Arn(entity_arn)
    account_number  = arn.get_account_number()
    entity_name     = arn.get_entity_name()

    policy_arn      =  'arn:aws:iam::{account_number}:policy/security-fairy/{entity_name}-security-fairy-revised-policy'\
                            .format(account_number=account_number,
                                    entity_name=entity_name)\
                                        .replace('_','-')
    logger.info(policy_arn)

    detach_policy(entity_name, policy_arn)
    delete_policy(policy_arn)


def detach_policy(entity_name, policy_arn):
    try:
        iam_client.detach_role_policy(RoleName=entity_name, PolicyArn=policy_arn)
    except Exception as error:
        loggin.info(error)


def delete_policy(policy_arn):

    iam_client      = SESSION.client('iam')
    policy_versions = iam_client.list_policy_versions( PolicyArn=policy_arn)['Versions']

    for version in policy_versions:
        if not version['IsDefaultVersion']:
            iam_client.delete_policy_version(   PolicyArn=policy_arn,
                                                VersionId=version['VersionId'])
    iam_client.delete_policy(PolicyArn=policy_arn)


def api_response(statusCode=500, headers={'Content-Type':'text/html'}, body='Internal Service Error'):
    if statusCode < 100 or statusCode > 599:
        raise ValueError('Invalid HTTP statusCode')

    return_value =  {
                'statusCode': statusCode,
                'headers'   : headers,
                'body'      : body
            }

    logger.info(return_value)
    return return_value


def nosql_to_list_of_dicts(dynamodb_response_item):
    refactored_dicts = []
    for item in dynamodb_response_item:
        refactored_item = {}
        for key in item:
            for nested_key in item[key]:
                refactored_item[key] = item[key][nested_key]
        refactored_dicts.append(refactored_item)
    return(refactored_dicts)


if __name__ == '__main__':
    # entity_arn = 'arn:aws:iam::281782457076:role/1s_tear_down_role'
    # disassociate_security_fairy_policy(entity_arn)
    # delete_policy('arn:aws:iam::281782457076:policy/security-fairy/1s-tear-down-role-security-fairy-revised-policy')
    # associate_preexisting_policies("arn:aws:iam::281782457076:role/1s_tear_down_role")
    # get_all_iam_audited_entities()
    # print(nosql_to_list_of_dicts(get_all_iam_audited_entities()))
    # event = {"resource":"/revert","path":"/revert","httpMethod":"POST","headers":None,"queryStringParameters":None,"pathParameters":None,"stageVariables":None,"requestContext":{"path":"/revert","accountId":"281782457076","resourceId":"l4irb8","stage":"test-invoke-stage","requestId":"test-invoke-request","identity":{"cognitoIdentityPoolId":None,"accountId":"281782457076","cognitoIdentityId":None,"caller":"AROAJFMSEYJPIQQGLKKO4:justiniravani","apiKey":"test-invoke-api-key","sourceIp":"test-invoke-source-ip","accessKey":"ASIAIGOR7BSSZ2T4WYUA","cognitoAuthenticationType":None,"cognitoAuthenticationProvider":None,"userArn":"arn:aws:sts::281782457076:assumed-role/1S-Admins/justiniravani","userAgent":"Apache-HttpClient/4.5.x (Java/1.8.0_131)","user":"AROAJFMSEYJPIQQGLKKO4:justiniravani"},"resourcePath":"/revert","httpMethod":"POST","apiId":"sloh70a4cj"},"body":"{\"entity_arn\":\"arn:aws:iam::281782457076:role/1s_tear_down_role\"}","isBase64Encoded":False}
    # lambda_handler(event, {})
