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


try:
    SESSION = boto3.session.Session(
        profile_name='sandbox',
        region_name='us-east-1'
    )
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()

def lambda_handler(events, context):
    s3_bucket = os.environ['s3_bucket']
    athena_client = SESSION.client('athena')

    output = 's3://{s3_bucket}/tables'.format(s3_bucket=s3_bucket)
    config = {
        'OutputLocation': output,
        'EncryptionConfiguration': {
            'EncryptionOption': 'SSE_S3'
        }
    }
    # ALTER TABLE cloudtrail_test ADD PARTITION (region='ap-northeast-2', year='2018', month='01', day='01')
    response = athena_client.start_query_execution(
        QueryString="create database if not exists logs;",
        ResultConfiguration=config
    )