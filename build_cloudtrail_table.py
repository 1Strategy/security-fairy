"""Build_Cloudtrail_Table

Create the CloudTrail Logs table for Athena use.

See the AWS documentation for Athena here:
    http://docs.aws.amazon.com/athena/latest/ug/getting-started.html
"""


import os
import sys
import json
import datetime
import logging
import boto3
from botocore.exceptions import ProfileNotFound


# These parameters should remain static
TIME                = datetime.datetime.utcnow()
AMZ_DATE            = TIME.strftime('%Y%m%dT%H%M%SZ')
DATE_STAMP          = TIME.strftime('%Y%m%d')
PROFILE             = 'sandbox'
LOG_LEVEL           = logging.DEBUG
SUCCESS = "SUCCESS"
FAILED  = "FAILED"

try:
    SESSION = boto3.session.Session(
        profile_name=PROFILE,
        region_name='us-east-1'
    )
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


try:
    from urllib2 import HTTPError, build_opener, HTTPHandler, Request
except ImportError:
    from urllib.error import HTTPError
    from urllib.request import build_opener, HTTPHandler, Request


def send(event, context, response_status, reason=None, response_data=None, physical_resource_id=None):
    response_data = response_data or {}
    response_body = json.dumps(
        {
            'Status': response_status,
            'Reason': reason or "See the details in CloudWatch Log Stream: " + context.log_stream_name,
            'PhysicalResourceId': physical_resource_id or context.log_stream_name,
            'StackId': event['StackId'],
            'RequestId': event['RequestId'],
            'LogicalResourceId': event['LogicalResourceId'],
            'Data': {'ConfigJson': response_data}
        }
    )
    logging.debug("Sending Response to CloudFormation")
    logging.debug(response_body)
    opener = build_opener(HTTPHandler)
    request = Request(event['ResponseURL'], data=response_body)
    request.add_header('Content-Type', '')
    request.add_header('Content-Length', len(response_body))
    request.get_method = lambda: 'PUT'
    response = opener.open(request)
    try:
        response = opener.open(request)
        print("Status code: {}".format(response.getcode()))
        print("Status message: {}".format(response.msg))
        return True
    except HTTPError as exc:
        print("Failed executing HTTP request: {}".format(exc.code))
        return False


def save_query(cloudtrail_logs_bucket):
    """Store the CloudTrail table creation query
    """
    athena = SESSION.client('athena')

    acct_number = SESSION.client('sts').get_caller_identity().get('Account')
    query_list = athena.list_named_queries()
    name_list = []

    for query in query_list.get("NamedQueryIds"):
        check = athena.get_named_query(
            NamedQueryId=query
        )
        name_list.append(check['NamedQuery'].get('Name'))

    if "cloudtrail_logs" in name_list:
        print("This query is already saved.")
    else:
        response = athena.create_named_query(
            Name="cloudtrail_logs",
            Description="Table of CloudTrail Logs created by Security Fairy.",
            Database="aws_logs",
            QueryString="""
create external table if not exists aws_logs.cloudtrail (
  eventVersion string,
  userIdentity
    struct<
      type: string,
      principalId: string,
      arn: string,
      accountId: string,
      userName: string,
      invokedBy: string,
      accesskeyid:string,
      sessioncontext:
        struct<
          attributes:
            struct<
              mfaauthenticated:string,
              creationdate:string
          >,
          sessionIssuer:
            struct<
              type:string,
              principalId:string,
              arn:string,
              accountId:string,
              userName:string
          >
      >
  >,
  eventTime string,
  eventSource string,
  eventName string,
  awsRegion string,
  sourceIPAddress string,
  userAgent string,
  errorCode string,
  errorMessage string,
  requestID string,
  eventID string,
  resources
    array<
      struct<
        ARN:string,
        accountId:string,
        type:string
      >
  >,
  eventType string,
  apiVersion string,
  readOnly boolean,
  recipientAccountId string,
  sharedEventID string,
  vpcEndpointId string
)
partitioned by (region STRING, year STRING, month STRING, day STRING)
row format serde 'com.amazon.emr.hive.serde.CloudTrailSerde'
stored as inputformat 'com.amazon.emr.cloudtrail.CloudTrailInputFormat'
outputformat 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
location 's3://{cloudtrail_bucket}/AWSLogs/{account_number}/CloudTrail/'
;""" \
.format(cloudtrail_bucket=cloudtrail_logs_bucket,
        account_number=acct_number)
        )

        return response


def build_database(s3_bucket):
    """Build the logs database in Athena
    """
    athena = SESSION.client('athena')

    output = 's3://{s3_bucket}/tables'.format(s3_bucket=s3_bucket)
    config = {
        'OutputLocation': output,
        'EncryptionConfiguration': {
            'EncryptionOption': 'SSE_S3'
        }
    }

    response = athena.start_query_execution(
        QueryString="create database if not exists logs;",
        ResultConfiguration=config
    )


def execute_cloudtrail_table_creation(s3_bucket):
    """Create the CloudTrail Logs table using the saved query
    """
    athena = SESSION.client('athena')

    query_list = athena.list_named_queries()
    name_list  = []
    output     = 's3://{s3_bucket}/tables'.format(s3_bucket=s3_bucket)
    config     = {
        'OutputLocation': output,
        'EncryptionConfiguration': {
            'EncryptionOption': 'SSE_S3'
        }
    }
    run_query = ''

    for query_id in query_list.get("NamedQueryIds"):
        query_obj = athena.get_named_query(
            NamedQueryId=query_id
        )
        query_details = query_obj['NamedQuery']
        if query_details.get('Name') == 'cloudtrail_logs':
            run_query = query_details.get('QueryString')

    response = athena.start_query_execution(
        QueryString=run_query,
        ResultConfiguration=config
    )

    return response


def lambda_handler(event, context):
    """Lambda Handler for Build_Cloudtrail_Table
    """
    logging.debug(json.dumps(event))

    # Setup Logging, delete other loggers
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=LOG_LEVEL, datefmt='%Y-%m-%dT%H:%M:%S')
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.debug("Environment Variables:")
    logging.info("Start Execution")

    try:
        cloudtrail_bucket = os.environ["cloudtrail_bucket"]

        log_level = os.environ.get('LOG_LEVEL','INFO') # Logging Level

        saved = save_query(cloudtrail_bucket)
        logging.debug(saved)

        db = build_database(cloudtrail_bucket)
        logging.debug(db)

        executed = execute_cloudtrail_table_creation(cloudtrail_bucket)
        logging.debug(executed)
        logging.info("Successful Execution")
        send(event, context, "SUCCESS")

    except Exception as error:
        logging.info("Failed Execution")
        logging.info(error)
        send(event, context, "FAILED")
        return "Error"


if __name__ == '__main__':
    lambda_handler({}, {})
