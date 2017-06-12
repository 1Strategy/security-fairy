import boto3
import time
import re
from botocore.exceptions import ClientError

# Create AWS session
try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()


def lambda_handler(event, context):

    event['execution_id'] = execute_query(event['entity_arn'], event['num_days'], event['s3_bucket'])
    return event


def execute_query(entity_arn, num_days, s3_bucket):

    escaped_arn = build_escaped_arn(entity_arn)

    # Query
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
    print(hql)

    output = 's3://{s3_bucket}/tables'.format(s3_bucket=s3_bucket)

    config = {
        'OutputLocation': output,
        'EncryptionConfiguration': {
            'EncryptionOption': 'SSE_S3'
        }
    }

    athena_client = session.client('athena')
    execution = athena_client.start_query_execution(QueryString=hql,
                                                    ResultConfiguration=config)

    print("Query ID:")
    print(execution['QueryExecutionId'])

    return execution['QueryExecutionId']



def build_escaped_arn(entity_arn):

    split_arn   = re.split('/|:', entity_arn)
    escaped_arn = "arn:aws:sts:" + split_arn[4] + ":assumed-role/\\" + split_arn[6]
    print(escaped_arn)
    return escaped_arn

if __name__ == '__main__':
    lambda_handler(
        {
            "entity_arn": "arn:aws:iam::281782457076:assumed-role/1s_tear_down_role",
            "num_days": "-30"
        },
        {}
    )
# if __name__ == '__main__':
#     build_escaped_arn('arn:aws:iam::281782457076:assumed-role/1s_tear_down_role')
