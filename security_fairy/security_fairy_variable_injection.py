"""Variable Injection

Creates the environment variables used
by subsequent Lambda functions in the
Security Fairy Step Functions Task.
"""


import os
import boto3


def lambda_handler(event, context):
    """ Executed by Lambda service.

    Define and return runtime-specific
    environment variables.
    """

    name = os.environ['AWS_LAMBDA_FUNCTION_NAME']
    region = os.environ['AWS_REGION']
    version = os.environ['AWS_LAMBDA_FUNCTION_VERSION']

    lambda_client = boto3.client('lambda', region_name=region)
    lambda_function = lambda_client.get_function(FunctionName=name, Qualifier=version)
    raw_env_vars = lambda_function['Configuration']['Environment']['Variables']

    for key, value in raw_env_vars.items():
        event[key] = value

    return event
