"""Build_Cloudtrail_Table

Create the CloudTrail Logs table for Athena use.

See the AWS documentation for Athena here:
    http://docs.aws.amazon.com/athena/latest/ug/getting-started.html
"""


import os
import sys
import json
import logging
import boto3
from datetime import datetime
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

    output = f"s3://{s3_bucket}/security-fairy-partition-queries"
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day
    regions = ['us-west-2',
                'us-west-1',
                'us-east-2',
                'us-east-1',
                'ap-south-1',
                'ap-northeast-2',
                'ap-southeast-1',
                'ap-southeast-2',
                'ap-northeast-1',
                'ca-central-1',
                'cn-north-1',
                'eu-central-1',
                'eu-west-1',
                'eu-west-2',
                'eu-west-3',
                'sa-east-1',
                'us-gov-west-1'
    ]
    config = {
        'OutputLocation': output,
        'EncryptionConfiguration': {
            'EncryptionOption': 'SSE_S3'
        }
    }

    for region in regions:
        try:
            response = athena_client.start_query_execution(
                QueryString=f"ALTER TABLE cloudtrail ADD PARTITION (region={region}, year={year}, month={month}, day={day})",
                ResultConfiguration=config
            )
            #change to logger
            print(response)
