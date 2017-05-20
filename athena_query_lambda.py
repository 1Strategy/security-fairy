import boto3
import time
from botocore.exceptions import ClientError

# Create AWS session
session = boto3.session.Session(profile_name='training')

# Connect to Athena
athena = session.client('athena')

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
    role = event.get('role')
    num_days = event.get('num_days')
    print(num_days)
    # Query
    hql = """
      select useridentity.arn as user_arn
           , eventsource
           , array_distinct(array_agg(eventName)) as actions
        from aws_logs.cloudtrail
       where date_parse(eventTime, '%Y-%m-%dT%TZ') >= current_date + interval '{num_days}' day
         and useridentity.arn = '{role}'
    group by eventsource
           , useridentity.arn
       limit 50
    """.format(num_days=num_days, role=role)
    print(hql)
    # Execute Query
    execution = athena.start_query_execution(QueryString=hql,
                                             ResultConfiguration=config
                                             )
    time.sleep(2)
    print("Okay, I've submitted your query. Here is the query ID:")
    print(execution['QueryExecutionId'])
    print("Please wait while your results are generated.")
    for _ in range(10):
        try:
            results = athena.get_query_results(QueryExecutionId=execution['QueryExecutionId'])
            print("Okay, thank you for waiting.")
            print("Here are the details about your results.")
            print("The Columns are:")
            cols = []
            for col in results["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]:
                cols.append(col["Name"])
            print("There were " + str(len(results["ResultSet"]["Rows"])) + "results.")
            for hit in results["ResultSet"]["Rows"]:
                print(cols)
                print(hit["Data"])
        except ClientError as e:
            print("Your results are not yet ready. Thank you for waiting.")
            time.sleep(0.5)
            print("How's your day going?")
            time.sleep(10)
            print(e.operation_name)


# print("I'm sorry. There was an error with your request.")
# print("I couldn't perform the operation: " + e.operation_name + ".")
# print("I believe this is the reason for this error:" + '\n' + str(e.args))


if __name__ == '__main__':
    lambda_handler(
        event={
            "role": "arn:aws:sts::281782457076:assumed-role/1S-Admins/alex",
            "num_days": "-7"
        },
        context=""
    )
