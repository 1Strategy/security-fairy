import logging
import pytest
import json
from security_fairy_tools import IAMPolicy
from security_fairy_tools import IAMStatement
from security_fairy_tools import Arn

logging_level = logging.INFO
# statement = IAMStatement('Allow',["pot:atosoup","goat:cheese"],'*', logging_level = logging_level)
# statement.get_statement()
# policy = IAMPolicy(logging_level = logging_level)
# policy.add_statement(statement)
# print(policy.print_policy())
# print(policy.get_policy())

# arn = Arn('arn:aws:iam::281782457076:role/1s_tear_down_role', logging_level = logging.DEBUG)
# arn = Arn('arn:aws:iam:us-east-1:842337631775:role/service-role/StatesExecutionRole-us-west-2')
policy = IAMPolicy(logging_level = logging_level)
policy.add_action('lambda:Invoke')
policy.add_action('lambda:Potato12356')
policy.add_action('ec2:RunInstances')
policy.add_action('ec2:StartInstances')
policy.add_action('monitoring:CreateAlarm')
print(policy.print_policy())

# arn = Arn('arn:aws:iam::281782457076:assumed-role/1s_tear_down_role/instance-1235', logging_level = logging.DEBUG)
# print(arn.is_role())
# print(arn.is_policy())
# print(arn.is_assumed_role())

def test_iam_policy_class():
    """Test Athena Query"""
    policy = IAMPolicy(logging_level = logging_level)
    policy.add_action('lambda:Invoke')
    policy.add_action('ec2:RunInstances')
    policy.add_action('ec2:StartInstances')
    policy.add_action('monitoring:CreateAlarm')
    print(policy.print_policy())
    assert policy.get_policy() == {"Version": "2012-10-17", "Statement": [{"Action": ["ec2:RunInstances", "ec2:StartInstances"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyEc2Policy"}, {"Action": ["cloudwatch:CreateAlarm"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyCloudwatchPolicy"}, {"Action": ["lambda:Invoke"], "Resource": "*", "Effect": "Allow", "Sid": "SecurityFairyLambdaPolicy"}]}
