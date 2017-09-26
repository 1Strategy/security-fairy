"""Email Approval Request

Sends an email to the user with an approval url.
"""


import boto3
import logging
from requests.utils import quote
from botocore.exceptions import ProfileNotFound
from setup_logger import create_logger

logger = create_logger(name="email_approval_request.py")

try:
    SESSION = boto3.session.Session(profile_name='training',
                                    region_name='us-east-1')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


def lambda_handler(event, context):
    """ Executed by the Lambda service.

    Sends an approval URL to the user via SNS.
    """

    execution_id = event['execution_id']
    task_token = quote(event['task_token'], safe='')
    api_endpoint = event['api_endpoint']

    approval_url = '{api_endpoint}approve?execution-id={execution_id}&task-token={tasktoken}'\
                    .format(api_endpoint=api_endpoint,
                            execution_id=execution_id,
                            tasktoken=task_token
                           )

    sns_client = SESSION.client('sns')
    sns_arn = event['sns_arn']

    # Build message
    message = 'Approve changes from Security Fairy here: {approval_url}'\
                .format(approval_url=approval_url)
    logger..debug(message)
    response = sns_client.publish(
        TopicArn=sns_arn,
        Message="{message}".format(message=message),
        Subject='Security Fairy Permissions Request')

    logger..debug(response)

if __name__ == '__main__':
    EVENT = {
        'execution_id':'f0774f6d-3986-4478-be43-23b62cfc65c0',
        'task_token': "AAAAKgAAAAIAAAAAAAAAAcMqTWc6Y9lUsccSZSoCCn8NOd71LbD98x2dU0LwJusNdxUOi7wwuwr4SmXXyCAfFIefCI/rnFfDeiOa4cN0uSF8a7uku4bN50BgFzcq7Aw1hY2V0rrE4KpSWJPVBUZ38LPwCXlvsFncAGOVRs9DDTj4docBIjwKjt2DBFEiaVQ6byk4zbsZlP0muYGNYR0gY9O6yh4Pf/zCfbRIvpZCiAdOV3kz2nkRH8YBCBCa1FvPPyPXWwlIsyL2ijdHC7G0//Xvv6ANmkYd9qCRwqSUYBm8nhTb0kFNWDBzsdEoEU9nFg2xWGvte7TaELVGGDVsk2y0YaDp4E6UwRiKNu0qIDeTA5OrpjVYurh/D3Pd06vc2aRpFQE9HxzCSJrg8lNS3jw3vLPXJzisourVu1SGZzHLOIEeqUDk4lWVGMylhm/EXefN2lmRC8p4NWIrtd9KrMJ3WlkrblS/aGzqCy3VRlmFITjHWws1+yvtBC0u3s99aYTvXXHylHCceE+EbL0qsES1qRrDtUdTHpJcB6MiaMf9Vbn2faa+OLJjnI8Y6J3uqFWl8yYFR41Cwc0RxH1RnsiQehwXLLiqvBSz4y+I5PI=",
        'api_endpoint': "https://gndl1fc1ii.execute-api.us-east-1.amazonaws.com/Prod",
        'sns_arn': 'arn:aws:sns:us-east-1:281782457076:security_fairy_topic'
        }
    lambda_handler(EVENT, {})
