import boto3
import time
from botocore.exceptions import ClientError

# Create AWS session
try:
    session = boto3.session.Session(profile_name='sandbox')
except Exception as e:
    session = boto3.session.Session()

# Connect to Athena
athena = session.client('athena', region_name='us-east-1')

# Get named query
queries = athena.list_named_queries()

# Query Configurations
config = {
    'OutputLocation': 's3://security-fairy',
    'EncryptionConfiguration': {
        'EncryptionOption': 'SSE_S3'
    }
}


def lambda_handler(event, context):
    return execute_query(event.get('entity_arn'), event.get('num_days'))


def execute_query(entity_arn, num_days):
    # Query
    hql = """
      select useridentity.arn as user_arn
           , eventsource
           , array_distinct(array_agg(eventName)) as actions
        from aws_logs.cloudtrail
       where date_parse(eventTime, '%Y-%m-%dT%TZ') >= current_date + interval '{num_days}' day
         and useridentity.arn = '{entity_arn}'
    group by eventsource
           , useridentity.arn
       limit 50
    """.format(num_days=num_days, entity_arn=entity_arn)

    # Execute Query
    execution = athena.start_query_execution(QueryString=hql,
                                             ResultConfiguration=config)

    print("Okay, I've submitted your query. Here is the query ID:")
    print(execution['QueryExecutionId'])
    print("Please wait while your results are generated.")

    return execution['QueryExecutionId']

if __name__ == '__main__':
    lambda_handler(
        {
            "entity_arn": "arn:aws:iam::281782457076:assumed-role/1s_tear_down_role",
            "num_days": "-7"
        },
        {}
    )
