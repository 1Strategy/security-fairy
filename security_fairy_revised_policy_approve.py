import boto3
import re
import os
from botocore.exceptions import ClientError

try:
    session = boto3.session.Session(profile_name='training', region_name='us-east-1')
except Exception:
    session = boto3.session.Session()


def lambda_handler(event, context):

    print(event)
    try:
        execution_id    = event['execution_id']
        dynamodb_table  = event.get('dynamodb_table', os.environ['dynamodb_table'])

        policy_object   = get_revised_policy(execution_id, dynamodb_table)
        entity_name     = get_entity_name_from_arn(policy_object['entity_arn'])


        existing_policies = get_existing_policies(entity_name)

        detach_existing_policies(entity_name, existing_policies)
        apply_revised_policy(policy_object)

    except Exception as error:
        print(error)


def apply_revised_policy(policy_object):

    print(policy_object)

    entity_arn  = policy_object['entity_arn']
    entity_name = get_entity_name_from_arn(entity_arn)
    policy      = policy_object['policy']

    print("Attaching: ")
    print("{}-security-fairy-revised-policy".format(entity_name).replace("_","-"))

    session.client('iam').put_role_policy(  RoleName=entity_name,
                                            PolicyName="{entity_name}-security-fairy-revised-policy".format(entity_name=entity_name).replace('_','-'),
                                            PolicyDocument=policy)


def get_existing_policies(entity_name):

    return session.client('iam').list_attached_role_policies(RoleName=entity_name)['AttachedPolicies']

def preserve_existing_policies(existing_policies, dynamodb_table):

    pass


def detach_existing_policies(entity_name, existing_policies):

    # existing_policies = session.client('iam').list_attached_role_policies(RoleName=entity_name)['AttachedPolicies']

    print("Detaching Policies: ")
    for policy in existing_policies:
        print(policy['PolicyArn'])
        session.client('iam').detach_role_policy(  RoleName=entity_name,
                                                   PolicyArn=policy['PolicyArn'])


def get_revised_policy(execution_id, dynamodb_table):

    return_response = {}
    try:
        dynamodb_response = session.client('dynamodb')\
                        .get_item(TableName=dynamodb_table,
                                  Key={
                                            "execution_id": {
                                                "S": execution_id
                                            }
                                        })
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
    lambda_handler({
        "execution_id": "c40e4cc1-a88d-4a99-8d54-6ffc0b07e4af"
    }, {})

# if __name__ == '__main__':
#     detach_existing_policies('arn:aws:iam::281782457076:role/1s_security_fairy_role')
# if __name__ == '__main__':
#     get_revised_policy('8d544e31-37af-4eb2-acf3-b5eda9f108bd')
# if __name__ == '__main__':
#     apply_revised_policy({'policy': u'{"Version": "2012-10-17", "Statement": [{"Action": ["ec2:DescribeAddresses"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyEc2"}, {"Action": ["logs:CreateLogStream"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyLogs1"}, {"Action": ["iam:GetGroup"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyIam"}, {"Action": ["lambda:ListFunctions20150331", "lambda:DeleteFunction20150331"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyLambda"}, {"Action": ["logs:CreateLogStream"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyLogs2"}, {"Action": ["logs:CreateLogGroup", "logs:CreateLogStream"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyLogs5"}, {"Action": ["kms:Decrypt"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyKms"}]}', 'entity_arn': u'arn:aws:iam::281782457076:role/1s_security_fairy_role'})
