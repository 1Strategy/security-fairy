"""Get Task Token

Retrieves the correct Task Token from the
Step Functions API, then updates the event
object for the next Lambda function.
"""


import boto3
from botocore.exceptions import ProfileNotFound

try:
    SESSION = boto3.session.Session(profile_name='training')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


def lambda_handler(event, context):
    """ Executed by the Lambda service.

    Returns an Event object that's been updated
    with the appropriate SNS Task Token.
    """
    sfn_client = SESSION.client('stepfunctions')
    activity_task = sfn_client.get_activity_task(activityArn=event['activity_arn'])
    event['task_token'] = activity_task['taskToken']

    return event
