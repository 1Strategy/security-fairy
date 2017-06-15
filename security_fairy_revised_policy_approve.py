import boto3
import time
import re
from botocore.exceptions import ClientError

try:
    session = boto3.session.Session(profile_name='training', region_name='us-east-1')
except Exception as e:
    session = boto3.session.Session()


def lambda_handler(event, context):

    print(event)
    try:
        execution_id    = event['execution_id']
        print(execution_id)
        policy_object   = get_revised_policy(execution_id)
        entity_name     = get_entity_name_from_arn(policy_object['entity_arn'])

        apply_revised_policy(policy_object)
        detach_existing_policies(entity_name)

    except Exception as error:
        print(error)


def apply_revised_policy(policy_object):

    print(policy_object)
    iam_client  = session.client('iam')

    entity_arn  = policy_object['entity_arn']
    entity_name = get_entity_name_from_arn(entity_arn)
    policy      = policy_object['policy']

    print("Attaching: ")
    print("{}-security-fairy-revised-policy".format(entity_name))

    iam_client.put_role_policy( RoleName=entity_name,
                                PolicyName="{entity_name}-security-fairy-revised-policy".format(entity_name=entity_name).replace('-','_'),
                                PolicyDocument=policy)


def detach_existing_policies(entity_name):
    iam_client = session.client('iam')

    attached_policies = iam_client.list_attached_role_policies(RoleName=entity_name)['AttachedPolicies']
    for policy in attached_policies:
        print("Detaching: ")
        print(policy['PolicyArn'])
        # iam_client.detach_role_policy(  RoleName=entity_name,
        #                                 PolicyArn=policy['PolicyArn'])


def get_revised_policy(execution_id):

    return_response = {}
    try:
        dynamodb_response = session.client('dynamodb') \
                        .get_item(  TableName='security_fairy_dynamodb_table',
                                    Key={
                                        "execution_id":{
                                            "S": execution_id
                                            }
                                        }
                                 )
        return_response['policy']       = dynamodb_response['Item']['new_policy']['S']
        return_response['entity_arn']   = dynamodb_response['Item']['entity_arn']['S']
        print(return_response)
        return return_response

    except Exception as e:
        print(e)
        raise ValueError('Execution Id doesn\'t exist or has expired. Security-fairy must be rerun.')


def get_entity_name_from_arn(entity_arn):
    entity_name = re.split('/|:', entity_arn)[5]
    return entity_name


if __name__ == '__main__':
    lambda_handler({"task_token": "AAAAKgAAAAIAAAAAAAAAAWCc/0ebSQGby/dUh0UmVoQaq5e7rLu2Otf33CR24g3tUU3YxlN5b25Xb42KwueRGbjZslgseVIF5x3Dg0kw9vMTziYrw0Mv0BhqgmEqWavee5bZlL4AmfFSW7lrQmfO/IjevsBBjJ/uIEX86HQ8v7SoygQJouuTyN8ViwDOErsepiKd5ee7PE1vcF5Aa9RGR/vD6elypRzcNWSnRjzfO4T60Z/G9Ig9uAFVqWWvIcUlt17SUZIG6toaCMMWQ/tm+13gSERKWHhZwFpL0EzV4TLN4DT7bDP9y7VUHqcyXRulL9+EDuQgLBy1dCUa9dyX0zcC2iSAXv7MrUliHXSHculk0nvu3u/aWPzDtRZl5MWdM+gBN6oEIIyBaLW+pQ9S6sRyi1BhtoWuBs4ev+bvqJdLtua51rP/78U7+5MkDhMg4b/VP6O4J+sQrwEMNa171hmzNcsC1zJzm7l9dRTFIVuMOTwz+5SWnse2wwc+mePcjqx1gfGQG7yvW9MAez18AdSzwPNPtcDvI4M12DPRAGNbjgXCIHeBWeKdv3arUX79ts5YJUB9fklKoTrf2J5lGf0adf2bJhlYwN4zH3Yqm9I=", "execution_id": "a6d34be0-683f-4c99-bc9e-0ca711e191b0"

    }, {})

# if __name__ == '__main__':
#     detach_existing_policies('arn:aws:iam::281782457076:role/1s_security_fairy_role')
# if __name__ == '__main__':
#     get_revised_policy('8d544e31-37af-4eb2-acf3-b5eda9f108bd')
# if __name__ == '__main__':
#     apply_revised_policy({'policy': u'{"Version": "2012-10-17", "Statement": [{"Action": ["ec2:DescribeAddresses"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyEc2"}, {"Action": ["logs:CreateLogStream"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyLogs1"}, {"Action": ["iam:GetGroup"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyIam"}, {"Action": ["lambda:ListFunctions20150331", "lambda:DeleteFunction20150331"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyLambda"}, {"Action": ["logs:CreateLogStream"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyLogs2"}, {"Action": ["logs:CreateLogGroup", "logs:CreateLogStream"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyLogs5"}, {"Action": ["kms:Decrypt"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyKms"}]}', 'entity_arn': u'arn:aws:iam::281782457076:role/1s_security_fairy_role'})
