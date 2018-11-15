"""Athena Query
Submits the appropriate Security Fairy
query to Athena.
"""


import re
import boto3
import logging
from setup_logger import create_logger
from botocore.exceptions import ProfileNotFound

logger = create_logger(name="athena_query.py", logging_level=logging.INFO)

try:
    SESSION = boto3.session.Session(profile_name='training',
                                    region_name='us-east-1')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


def lambda_handler(event, context):
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

    hql = f"""
       select useridentity.arn as user_arn
            , eventsource
            , array_distinct(array_agg(eventName)) as actions
         from aws_logs.cloudtrail
        where date_parse(eventTime, '%Y-%m-%dT%TZ') >= current_date + interval '{num_days}' day
          and regexp_like(useridentity.arn, '{escaped_arn}\/.+')
     group by useridentity.arn
            , eventsource
          """
    logger.info(hql)

    output = f's3://{s3_bucket}/tables'
    config = {
        'OutputLocation': output,
        'EncryptionConfiguration': {
            'EncryptionOption': 'SSE_S3'
        }
    }

    athena_client = SESSION.client('athena')
    execution = athena_client.start_query_execution(QueryString=hql,
                                                    ResultConfiguration=config)
    logger.info("Query ID:")
    logger.info(execution['QueryExecutionId'])

    return execution['QueryExecutionId']


def build_escaped_arn(entity_arn):
    """Format ARN"""

    split_arn = re.split('/|:', entity_arn)
    escaped_arn = "arn:aws:sts::" + split_arn[4] + ":assumed-role\\/" + split_arn[6]
    logger.debug(escaped_arn)
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
