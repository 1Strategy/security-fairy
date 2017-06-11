
import boto3
import json
import datetime
from requests.utils import quote

try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()

# Use the Boto3 SDK to create a client to call SNS functions

def lambda_handler(event, context):


    execution_id    = event['execution_id']
    task_token      = quote(event['task_token'],safe='')
    api_endpoint    = event['api_endpoint']

    approval_url    = '{api_endpoint}/approve?execution-id={execution_id}&task-token={tasktoken}' \
                            .format(api_endpoint=api_endpoint,execution_id=execution_id, tasktoken = task_token)

    sns_client = session.client('sns')
    sns_arn =  event['sns_arn']

    # Build message
    message = 'Approve changes from Security Fairy here: {approval_url}'.format(approval_url=approval_url)
    print(message)
    response = sns_client.publish( TopicArn=sns_arn,
                        Message="{message}".format(message=message),
                        Subject='Security Fairy Permissions Request')
    print(response)

if __name__ == '__main__':
    event = {
                'execution_id':'8d544e31-37af-4eb2-acf3-b5eda9f108bd',
                'task_token': """AAAAKgAAAAIAAAAAAAAAAeJQPfCu%2BAfXzcoGPeaqmKRC6Brfruxg6e55DKawq7QageiGyz%2BxgByX6oojCaQ%2FCbBfXF9Z5QS1%2FUOQtJ7eelhpo33TCE9%2BEg5%2BM83xybrzZI2Vs1%2BnxyRA1jxiskrPugub285HxiU%2Fy1HYxXjs5mIPiH4d4F0QtaXLW%2BOD09PyBnymReiLZ7yZDn2EEtrGhBPNk6eriXGqeJVheLmt8nZpv27Z0rRPH%2B9GCfSJC6fLK7THguQfghL65gHNqmB2PCCL0NHAeRCE2v6PqFPscbjXIkM%2F9BsW1vZRzZ4re%2FO6luXT84iObpdnlHzosCgIIgFlqXAqfQJPM7ZJ%2FXmRRvZadB8UF%2F%2FiDcFS8Busqn4t0HIbCJY%2FuFfeuOhSSW2U%2BCTitv5QPdtfn5ar3ZmKhey9fGrjItV9DJNQt60QCvQhVh4piRcxPBUlyYg%2FhksY8lKoeRKZk7GJWCX5Tml5zUmWw3JP2XM68But2u%2BtH0hqnv7%2BolhTPY6uKh%2FJQ3zXSqZ%2BANJQYuZtV48kTEkfb7YUKsJOFA8P4rfhnjZBoi8Aze%2BwatWUIxkBYBPrXpefpQ%3D%3D""",
                'api_endpoint': "https://byv5cb80g2.execute-api.us-west-2.amazonaws.com/prod",
                'sns_arn': 'arn:aws:sns:us-west-2:281782457076:security_fairy_topic'


            }
    lambda_handler(event, {})
