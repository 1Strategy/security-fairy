import os
import boto3

def lambda_handler(event, context):

    name    = os.environ['AWS_LAMBDA_FUNCTION_NAME']
    region  = os.environ['AWS_REGION']
    version = os.environ['AWS_LAMBDA_FUNCTION_VERSION']

    lambda_client   = boto3.client('lambda', region_name=region)
    raw_env_vars    = lambda_client.get_function(FunctionName=name, Qualifier=version)['Configuration']['Environment']['Variables']

    for key, value in raw_env_vars.items():
        event[key] = value

    return event
