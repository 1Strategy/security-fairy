import boto3
import gzip
import json
import logging
import os
import re
from security_fairy_tools import Arn

logging.basicConfig(level=logging.INFO)

def lambda_handler(event, context):

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
    # write_denied_actions_to_dynamodb(access_denied_records, dynamodb_table)
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
    dynamodb_client = boto3.client('dynamodb', region_name = 'us-east-1')
    response = dynamodb_client.scan(
                            TableName=dynamodb_table,
                            IndexName='entity_arn',
                            AttributesToGet=[
                                'execution_id',
                            ],
                            Select='ALL_ATTRIBUTES'|'ALL_PROJECTED_ATTRIBUTES'|'SPECIFIC_ATTRIBUTES'|'COUNT',
                            ScanFilter={
                                'string': {
                                    'AttributeValueList': [
                                        {
                                            'S': 'string',
                                            'N': 'string',
                                            'B': b'bytes'
                                        }
                                    ],
                                    'ComparisonOperator': 'EQ'|'NE'|'IN'|'LE'|'LT'|'GE'|'GT'|'BETWEEN'|'NOT_NULL'|'NULL'|'CONTAINS'|'NOT_CONTAINS'|'BEGINS_WITH'
                                }
                            }
                        )


    existing_denied_actions = dynamodb_client.get_item( TableName=dynamodb_table,
                                                        Key={
                                                                "execution_id": {
                                                                    "S": execution_id
                                                                }
                                                            }
                                                        )['Items']


    for record in access_denied_records:
        if is_access_denied_security_fairy_audited_role(record['arn']):
            if not record['denied_action'] in existing_denied_actions:
                pass
                # dynamodb_client.update_item(TableName=dynamodb_table,
                #                             Key={
                #                                 "execution_id": {
                #                                     "S": execution_id
                #                                 }
                #                             },
                #                             AttributeUpdates={
                #                                 "existing_policies": {
                #                                     "Value":{"SS": existing_policies}
                #                                 }})


def is_access_denied_security_fairy_audited_role(role_arn):

    iam_client  = boto3.client('iam')
    #Consumes an role arn and examines its attached policies to see
    #if they were created by security-fairy
    role        = Arn(role_arn)
    role_name   = role.get_entity_name()

    logging.debug(role_name)

    attached_policies = iam_client.list_role_policies(RoleName=role_name)

    # Examines all attached policies and search for an attached policy with the
    # following format:  *_security_fairy_revised_policy
    # (see security_fairy_revised_policy_approve.py line 58)

    for policy in attached_policies:
        logging.debug(policy)
        if '_security_fairy_revised_policy' in policy:
            return True

    return False


if __name__ == '__main__':
    EVENT = {
              "Records": [
                {
                  "eventVersion": "2.0",
                  "eventTime": "2017-08-23T17:27:20.482Z",
                  "requestParameters": {
                    "sourceIPAddress": "184.72.102.183"
                  },
                  "s3": {
                    "configurationId": "log_posted",
                    "object": {
                      "eTag": "f88cc0ba387febb9d1922bcf3624e249",
                      "sequencer": "00599DBAF77B4804AE",
                      "key": "AWSLogs/281782457076/CloudTrail/us-east-1/2017/08/23/281782457076_CloudTrail_us-east-1_20170823T1725Z_Nobz9PDTfkS2itSG.json.gz",
                      "size": 4342
                    },
                    "bucket": {
                      "arn": "arn:aws:s3:::1strategy-training-traillogs",
                      "name": "1strategy-training-traillogs",
                      "ownerIdentity": {
                        "principalId": "A3F4AZ9K861LVS"
                      }
                    },
                    "s3SchemaVersion": "1.0"
                  },
                  "responseElements": {
                    "x-amz-id-2": "qakr7pYcVWfsXM/BEncmZ/zQVPQnIAyN5ggRIF+9/+5JhAhhmMDZDJunlhhFowOKzGF9mNtF1Ys=",
                    "x-amz-request-id": "5A68EDF6D1F0C933"
                  },
                  "awsRegion": "us-west-2",
                  "eventName": "ObjectCreated:Put",
                  "userIdentity": {
                    "principalId": "AWS:AROAI6ZMWVXR3IZ6MKNSW:i-0c91c32104e81c79d"
                  },
                  "eventSource": "aws:s3"
                }
              ]
            }
    lambda_handler(EVENT, {})
