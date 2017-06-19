"""Revised Policy Approve

Implements the changes suggested by Security
Fairy. Detaches the existing policy for the
queried role and attaches the revised policy.
"""


import re
import boto3
from botocore.exceptions import ProfileNotFound

try:
    SESSION = boto3.session.Session(profile_name='training')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


def lambda_handler(event, context):
    """ Executed by the Lambda service.

    Detaches the existing managed policies from the
    queried role and attaches the Security Fairy
    revised policy.
    """

    try:
        execution_id = event['execution_id']
        policy_object = get_revised_policy(execution_id)
        entity_name = get_entity_name_from_arn(policy_object['entity_arn'])

        apply_revised_policy(policy_object)
        detach_existing_policies(entity_name)

    except Exception as error:
        print error


def apply_revised_policy(policy_object):
    """Attach Security Fairy's suggested policy"""

    iam_client = SESSION.client('iam')

    entity_arn = policy_object['entity_arn']
    policy = policy_object['policy']
    entity_name = get_entity_name_from_arn(entity_arn)

    format_name = "{entity_name}_security_fairy_revised_policy".format(
        entity_name=entity_name
        )

    print "Attaching: "
    print format_name

    iam_client.put_role_policy(
        RoleName=entity_name,
        PolicyName=format_name,
        PolicyDocument=policy
        )


def detach_existing_policies(entity_name):
    """Detach existing managed policies"""

    iam_client = SESSION.client('iam')

    role_policies = iam_client.list_attached_role_policies(RoleName=entity_name)
    attached_policies = role_policies['AttachedPolicies']

    for policy in attached_policies:
        print "Detaching: "
        print policy['PolicyArn']
        # iam_client.detach_role_policy(RoleName=entity_name,
        #                               PolicyArn=policy['PolicyArn']
        #                              )


def get_revised_policy(execution_id):
    """Retrieve Security Fairy's suggested policy"""

    return_response = {}
    try:
        dynamodb = SESSION.client('dynamodb', region_name='us-west-2')
        dynamodb_response = dynamodb.get_item(TableName='security_fairy_pending_approval',
                                              Key={
                                                  "id": {
                                                      "S": execution_id
                                                      }
                                                  }
                                             )
        return_response['policy'] = dynamodb_response['Item']['new_policy']['S']
        return_response['entity_arn'] = dynamodb_response['Item']['entity_arn']['S']
        return return_response

    except Exception as e:
        print e
        raise ValueError('Execution Id doesn\'t exist or has expired. \
                          Security-fairy must be rerun.'
                        )


def get_entity_name_from_arn(entity_arn):
    """Parse entity name from ARN"""

    new_name = re.split('/|:', entity_arn)[5]
    entity_name = new_name.replace('-', '_')
    return entity_name


if __name__ == '__main__':
    lambda_handler({
        'exeuction_id':'8d544e31-37af-4eb2-acf3-b5eda9f108bd'
    }, {})

# if __name__ == '__main__':
#     detach_existing_policies('arn:aws:iam::281782457076:role/1s_security_fairy_role')
# if __name__ == '__main__':
#     get_revised_policy('8d544e31-37af-4eb2-acf3-b5eda9f108bd')
# if __name__ == '__main__':
#     apply_revised_policy({'policy': u'{"Version": "2012-10-17", "Statement": [{"Action": ["ec2:DescribeAddresses"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyEc2"}, {"Action": ["logs:CreateLogStream"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyLogs1"}, {"Action": ["iam:GetGroup"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyIam"}, {"Action": ["lambda:ListFunctions20150331", "lambda:DeleteFunction20150331"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyLambda"}, {"Action": ["logs:CreateLogStream"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyLogs2"}, {"Action": ["logs:CreateLogGroup", "logs:CreateLogStream"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyLogs5"}, {"Action": ["kms:Decrypt"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyBuiltPolicyKms"}]}', 'entity_arn': u'arn:aws:iam::281782457076:role/1s_security_fairy_role'})
