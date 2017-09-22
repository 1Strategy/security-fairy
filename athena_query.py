"""Athena Query
Submits the appropriate Security Fairy
query to Athena.
"""


import re
import boto3
import logging
from aws_session_manager import AWS_Session
from botocore.exceptions import ProfileNotFound

logging_level = logging.INFO
logging.basicConfig(level=logging_level)

try:
    SESSION = boto3.session.Session(profile_name='training',
                                    region_name='us-east-1')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()

# SESSION = AWS_Session()

def lambda_handler(event, context):
    # global SESSION
    # SESSION = SESSION.get_session()
    """ Executed by the Lambda service.
    Submits the query for execution and returns
    the Execution ID for use by subsequent
    Lambda functions.
    """

    event['execution_id'] = execute_query(event['entity_arn'],
                                          event['num_days'],
                                          event['s3_bucket'])

    return event


def execute_query(entity_arn, num_days, s3_bucket):
    """Submit and run query"""

    escaped_arn = build_escaped_arn(entity_arn)

    hql = """
       select useridentity.arn as user_arn
            , eventsource
            , array_distinct(array_agg(eventName)) as actions
         from aws_logs.cloudtrail
        where date_parse(eventTime, '%Y-%m-%dT%TZ') >= current_date + interval '{num_days}' day
          and regexp_like(useridentity.arn, '{escaped_arn}\/.+')
     group by useridentity.arn
            , eventsource
          """.format(num_days=num_days, escaped_arn=escaped_arn)
    print hql

    output = 's3://{s3_bucket}/tables'.format(s3_bucket=s3_bucket)
    config = {
        'OutputLocation': output,
        'EncryptionConfiguration': {
            'EncryptionOption': 'SSE_S3'
        }
    }

    athena_client = SESSION.client('athena')
    execution = athena_client.start_query_execution(QueryString=hql,
                                                    ResultConfiguration=config)
    print("Query ID:")
    print(execution['QueryExecutionId'])

    return execution['QueryExecutionId']


def build_escaped_arn(entity_arn):
    """Format ARN"""

    split_arn = re.split('/|:', entity_arn)
    escaped_arn = "arn:aws:sts::" + split_arn[4] + ":assumed-role\\/" + split_arn[6]
    logging.debug(escaped_arn)
    return escaped_arn

if __name__ == '__main__':
    # arn:aws:sts::281782457076:assumed-role\/1s_tear_down_role\/.+

    lambda_handler(
        {
            "entity_arn": "arn:aws:iam::281782457076:assumed-role/1s_tear_down_role",
            "num_days": "-30",
            "s3_bucket": "1s-potato-east"
        },
        {}
    )
