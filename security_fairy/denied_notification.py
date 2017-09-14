import boto3
import gzip
import json
import logging
import os
import re
from tools import Arn
from aws_session_manager import AWS_Session
from botocore.exceptions import ProfileNotFound

logging.basicConfig(level=logging.INFO)

try:
    SESSION = boto3.session.Session(profile_name='training',
                                    region_name='us-east-1')

except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


def lambda_handler(event, context):
    # global SESSION
    # SESSION = SESSION.get_session()
    topic_arn       = os.environ.get('sns_arn', 'arn:aws:sns:us-east-1:281782457076:security_fairy_topic')
    dynamodb_table  = os.environ.get('dynamodb_table', 'arn:aws:dynamodb:us-east-1:281782457076:table/security_fairy_dynamodb_table')
    # Extract Bucket and Key from an SNS notification
    # message = json.loads(event['Records'][0]['Sns']['Message'])
    # bucket  = message['s3Bucket']
    # key     = message['s3ObjectKey'][0]

    # Extracted Bucket and Key from S3 event notification
    bucket  = event['Records'][0]['s3']['bucket']['name']
    key     = event['Records'][0]['s3']['object']['key']

    # where to save the downloaded file
    file_path = '/tmp/cloudtraillogfile.gz'

    # downloads file to above path
    boto3.client('s3').download_file(bucket, key, file_path)

    # opens gz file for reading
    gzfile  = gzip.open(file_path, 'r')

    # loads contents of the Records key into variable (our actual cloudtrail log entries!)
    records = json.loads(gzfile.readlines()[0])['Records']

    access_denied_records = check_records_for_error_code(records)
    security_fairy_access_denied_records = get_security_fairy_audited_entities(access_denied_records)
    write_denied_actions_to_dynamodb(security_fairy_access_denied_records, dynamodb_table)
    send_access_denied_notifications(access_denied_records, topic_arn)


def check_records_for_error_code(records, error_codes = ['AccessDenied', 'AccessDeniedException','Client.UnauthorizedOperation']):

    matched_error_records = []

    for record in records:
        if record.get('errorCode', None) in error_codes:
            logging.debug(record)
            extracted_information = {}
            arn             = Arn(record['userIdentity'].get('arn', None))
            role_name       = arn.get_entity_name()
            service_name    = arn.get_service()
            extracted_information['arn']            = arn.get_full_arn()
            extracted_information['error_code']     = record['errorCode']
            extracted_information['denied_action']  = service_name + ':' + record['eventName']

            if not extracted_information in matched_error_records:
                logging.debug('extracted_information doesn\'t already exist in list of access denieds')
                matched_error_records.append(extracted_information)

    logging.debug(matched_error_records)
    return matched_error_records


def send_access_denied_notifications(access_denied_records, topic_arn):

    if access_denied_records:
        response = boto3.client('sns', region_name = 'us-east-1')\
                            .publish(   TopicArn=topic_arn,
                                        Message=json.dumps(access_denied_records),
                                        Subject='Automated AWS Notification - Access Denied')


def write_denied_actions_to_dynamodb(access_denied_records, dynamodb_table):
    #take in the below:
    # [{"error_code": "AccessDenied", "arn": "arn:aws:sts::281782457076:assumed-role/serverless_api_gateway_step_functions/BackplaneAssumeRoleSession", "denied_action": "states:StartExecution"}, {"error_code": "AccessDenied", "arn": "arn:aws:sts::281782457076:assumed-role/serverless_api_gateway_step_functions/BackplaneAssumeRoleSession", "denied_action": "states:StartExecution"}]
    # read the dynamodb_table, if the action already exists, do nothing
    dynamodb_client = SESSION.client('dynamodb')

    for record in access_denied_records:
        entity_arn = record['arn']
        execution_id, existing_denied_actions = get_existing_denied_actions(entity_arn, dynamodb_table)
        updated_denied_actions  = existing_denied_actions

        if not record['denied_action'] in existing_denied_actions:
            updated_denied_actions.append(record['denied_action'])

        dynamodb_client.update_item(TableName=dynamodb_table,
                                    Key={
                                        "execution_id": {
                                            "S": execution_id
                                        }
                                    },
                                    AttributeUpdates={
                                        "denied_actions": {
                                            "Value":{"SS": updated_denied_actions}
                                        }
                                    })

def get_security_fairy_audited_entities(access_denied_records):

    audited_entities = []
    for record in access_denied_records:
        entity      = Arn(record['arn'])
        entity.convert_assumed_role_to_role()
        entity_arn  = entity.get_full_arn()
        logging.debug(entity_arn)
        if entity.is_role() and is_access_denied_security_fairy_audited_role(entity_arn):
            logging.debug('Adding access_denied_record to list')
            record['arn'] = entity_arn
            audited_entities.append(record)

    logging.info(audited_entities)
    return audited_entities


def get_existing_denied_actions(entity_arn, dynamodb_table):
    dynamodb_client = SESSION.client('dynamodb')
    response = dynamodb_client.scan(
                            TableName=dynamodb_table,
                            IndexName='entity_arn',
                            AttributesToGet=[
                                'execution_id',
                                'entity_arn',
                                'denied_actions'
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

    existing_denied_actions = [] if response.get('denied_actions') is None else response['denied_actions']['SS']

    execution_id            = response['execution_id']['S']
    logging.info(existing_denied_actions)

    return execution_id, existing_denied_actions


def is_access_denied_security_fairy_audited_role(role_arn):

    iam_client  = SESSION.client('iam')
    #Consumes an role arn and examines its attached policies to see
    #if they were created by security-fairy
    role        = Arn(role_arn)
    role_name   = role.get_entity_name()

    logging.info(role_name)
    attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)

    # Examines all attached policies and search for an attached policy with the
    # following format:  *_security_fairy_revised_policy
    # (see security_fairy_revised_policy_approve.py line 58)
    logging.debug(attached_policies)
    for policy in attached_policies['AttachedPolicies']:
        logging.info(policy['PolicyName'])
        if '-security-fairy-revised-policy' in policy['PolicyName']:
            return True

    return False

if __name__ == '__main__':
    # arn = 'arn:aws:iam::281782457076:role/1s_tear_down_role'
    # logging.info(is_access_denied_security_fairy_audited_role(arn))
    access_denied_records = [{"error_code": "AccessDenied", "arn": "arn:aws:sts::281782457076:assumed-role/serverless_api_gateway_step_functions/BackplaneAssumeRoleSession", "denied_action": "states:StartExecution"},
                             {"error_code": "AccessDenied", "arn": "arn:aws:sts::281782457076:assumed-role/1s_tear_down_role/potato", "denied_action": "route53:CreateHostedZone"},
                             {"error_code": "AccessDenied", "arn": "arn:aws:iam::281782457076:user/dbrewer@experlogix.com", "denied_action": "codebuild:StartBuild"},
                             {"error_code": "AccessDenied", "arn": "arn:aws:iam::281782457076:user/tj.eaglescout@gmail.com", "denied_action": "codebuild:StartBuild"},
                             {"error_code": "AccessDenied", "arn": "arn:aws:iam::281782457076:user/chase.thompson-baugh@simplymac.com", "denied_action": "codebuild:StartBuild"},
                             {"error_code": "AccessDenied", "arn": "arn:aws:iam::281782457076:user/steven.nourse@vivintsolar.com", "denied_action": "codebuild:StartBuild"},
                             {"error_code": "AccessDenied", "arn": "arn:aws:iam::281782457076:role/1s_tear_down_role", "denied_action": "codebuild:StartBuild"}]
    # dynamodb_table = 'security_fairy_dynamodb_table'
    # existing_denied_actions('arn:aws:iam::281782457076:role/1s_tear_down_role', dynamodb_table)
    security_fairy_access_denied_records = get_security_fairy_audited_entities(access_denied_records)
    write_denied_actions_to_dynamodb(security_fairy_access_denied_records,'security_fairy_dynamodb_table')

# if __name__ == '__main__':
#     EVENT = {
#               "Records": [
#                 {
#                   "eventVersion": "2.0",
#                   "eventTime": "2017-08-23T17:27:20.482Z",
#                   "requestParameters": {
#                     "sourceIPAddress": "184.72.102.183"
#                   },
#                   "s3": {
#                     "configurationId": "log_posted",
#                     "object": {
#                       "eTag": "f88cc0ba387febb9d1922bcf3624e249",
#                       "sequencer": "00599DBAF77B4804AE",
#                       "key": "AWSLogs/281782457076/CloudTrail/us-east-1/2017/08/23/281782457076_CloudTrail_us-east-1_20170823T1725Z_Nobz9PDTfkS2itSG.json.gz",
#                       "size": 4342
#                     },
#                     "bucket": {
#                       "arn": "arn:aws:s3:::1strategy-training-traillogs",
#                       "name": "1strategy-training-traillogs",
#                       "ownerIdentity": {
#                         "principalId": "A3F4AZ9K861LVS"
#                       }
#                     },
#                     "s3SchemaVersion": "1.0"
#                   },
#                   "responseElements": {
#                     "x-amz-id-2": "qakr7pYcVWfsXM/BEncmZ/zQVPQnIAyN5ggRIF+9/+5JhAhhmMDZDJunlhhFowOKzGF9mNtF1Ys=",
#                     "x-amz-request-id": "5A68EDF6D1F0C933"
#                   },
#                   "awsRegion": "us-west-2",
#                   "eventName": "ObjectCreated:Put",
#                   "userIdentity": {
#                     "principalId": "AWS:AROAI6ZMWVXR3IZ6MKNSW:i-0c91c32104e81c79d"
#                   },
#                   "eventSource": "aws:s3"
#                 }
#               ]
#             }
#     lambda_handler(EVENT, {})
