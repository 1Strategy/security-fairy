import boto3
import gzip
import json
import logging
import os
import re
from security_fairy_tools import Arn

logging.basicConfig(level=logging.DEBUG)

def lambda_handler(event, context):

    topic_arn = os.environ['sns_arn']

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
            # role_name       = re.split('/|:', record['userIdentity'].get('arn', ':::::/NoRole'))[6]
            # service_name    = record['eventSource'].split('.')[0]

            # extracted_information['arn']            = record['userIdentity'].get('arn','NoRole')
            extracted_information['arn']            = arn.get_full_arn()
            extracted_information['error_code']     = record['errorCode']
            extracted_information['denied_action']  = service_name + ':' + record['eventName']

            access_denied_records.append(extracted_information)

    logging.debug(access_denied_records)

    if access_denied_records:
        response = boto3.client('sns', region_name = 'us-east-1')\
                        .publish(   TopicArn=topic_arn,
                                    Message=json.dumps(access_denied_records),
                                    Subject='Automated AWS Notification - Access Denied')

if __name__ == '__main__':
    EVENT = {}
    lambda_handler(EVENT, {})
