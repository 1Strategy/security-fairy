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
TIME       = datetime.datetime.utcnow()
AMZ_DATE   = TIME.strftime('%Y%m%dT%H%M%SZ')
DATE_STAMP = TIME.strftime('%Y%m%d')
PROFILE    = 'sandbox'
# need to find cloudtrail bucket with the CloudTrail API
# in boto3: describe_trails()[trailList].get("S3BucketName")

# Build in Sandbox:
cloudtrail_bucket = "1strategy-sandbox.cloudtrial"

# Build in Training:
# cloudtrail_bucket = "1strategy-training-traillogs"

def create_session():
    """Establish an AWS session through boto3
    """
    try:
        session = boto3.session.Session(
            profile_name=PROFILE,
            region_name='us-east-1'
        )
    except ProfileNotFound as pnf:
        session = boto3.session.Session(region_name='us-east-1')

    return session


def save_query(sdk_session, cloudtrail_logs_bucket):
    """Store the CloudTrail table creation query
    """
    if sdk_session.get_credentials()._is_expired():
        sdk_session = create_session()
        athena = sdk_session.client('athena')
    else:
        athena = sdk_session.client('athena')

    acct_number = sdk_session.client('sts').get_caller_identity().get('Account')
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
            Database="logs",
            QueryString="""
create external table if not exists logs.cloudtrail (
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
row format serde 'com.amazon.emr.hive.serde.CloudTrailSerde'
stored as inputformat 'com.amazon.emr.cloudtrail.CloudTrailInputFormat'
outputformat 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
location 's3://{cloudtrail_bucket}/AWSLogs/{account_number}/CloudTrail/'
;""" \
.format(cloudtrail_bucket=cloudtrail_logs_bucket,
        account_number=acct_number)
        )
        
        return response


def build_database(sdk_session, s3_bucket):
    """Build the logs database in Athena
    """
    if sdk_session.get_credentials()._is_expired():
        sdk_session = create_session()
        athena = sdk_session.client('athena')
    else:
        athena = sdk_session.client('athena')

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


def execute_cloudtrail_table_creation(sdk_session, s3_bucket):
    """Create the CloudTrail Logs table using the saved query
    """
    if sdk_session.get_credentials()._is_expired():
        sdk_session = create_session()
        athena = sdk_session.client('athena')
    else:
        athena = sdk_session.client('athena')

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
    log_level = os.environ.get('LOG_LEVEL','INFO') # Logging Level
    # Setup Logging, delete other loggers
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=log_level, datefmt='%Y-%m-%dT%H:%M:%S')
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.debug("Environment Variables:")
    logging.info("Start Execution")

    sess = create_session()

    saved = save_query(sess, cloudtrail_bucket)
    logging.debug(saved)
    
    db = build_database(sess, '1s-data-lake')
    logging.debug(db)
    
    executed = execute_cloudtrail_table_creation(sess, '1s-data-lake')
    logging.debug(executed)
    
    logging.info("End Execution")


if __name__ == '__main__':
    lambda_handler({}, {})
