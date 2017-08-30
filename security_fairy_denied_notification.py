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
    access_denied_records = []

    for record in records:
        if record.get('errorCode', None) in ['AccessDenied', 'AccessDeniedException','Client.UnauthorizedOperation']:
            logging.debug(record)
            extracted_information = {}
            arn             = Arn(record['userIdentity'].get('arn', None))
            role_name       = arn.get_entity_name()
            service_name    = arn.get_service()
            extracted_information['arn']            = arn.get_full_arn()
            extracted_information['error_code']     = record['errorCode']
            extracted_information['denied_action']  = service_name + ':' + record['eventName']

            if not extracted_information in access_denied_records:
                logging.debug('extracted_information doesn\'t already exist in list of access denieds')
                access_denied_records.append(extracted_information)



    logging.debug(access_denied_records)

    if access_denied_records:
        response = boto3.client('sns', region_name = 'us-east-1')\
                        .publish(   TopicArn=topic_arn,
                                    Message=json.dumps(access_denied_records),
                                    Subject='Automated AWS Notification - Access Denied')

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
