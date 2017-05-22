import boto3


# Create AWS session
try:
    session = boto3.session.Session(profile_name='sandbox')
except Exception as e:
    session = boto3.session.Session()

# Connect to Athena
athena = session.client('athena', region_name='us-east-1')


def lambda_handler(event, context):
    # You must submit the AWS account number within the event parameter
    # Run the create cloudtrail table query
    creation = athena.start_query_execution(QueryString=create_table,
                                            ResultConfiguration=config
                                            )
    return creation


# Query Configurations
config = {
    'OutputLocation': 's3://security-fairy/tables/',
    'EncryptionConfiguration': {
        'EncryptionOption': 'SSE_S3'
    }
}

create_table = """
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
row format serde 'com.amazon.emr.hive.serde.CloudTrailSerde'
stored as inputformat 'com.amazon.emr.cloudtrail.CloudTrailInputFormat'
outputformat 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
location 's3://1strategy-training-traillogs/AWSLogs/{account_number}/CloudTrail/'
;
""".format(account_number=event.get(accountId))
