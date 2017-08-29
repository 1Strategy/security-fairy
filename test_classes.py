import logging
from security_fairy_tools import IAMPolicy
from security_fairy_tools import IAMStatement
from security_fairy_tools import Arn
logging_level = logging.INFO
statement = IAMStatement('Allow',["pot:atosoup","goat:cheese"],'*', logging_level = logging_level)
statement.get_statement()
policy = IAMPolicy(logging_level = logging_level)
policy.add_statement(statement)
print(policy.print_policy())
print(policy.get_policy())

# arn = Arn('arn:aws:iam::281782457076:role/1s_tear_down_role', logging_level = logging.DEBUG)
arn = Arn('arn:aws:iam:us-east-1:842337631775:role/service-role/StatesExecutionRole-us-west-2')
print("full_arn: "      + arn.get_full_arn())
print("entity_name: "   + arn.get_entity_name())
print("entity_type: "   + arn.get_entity_type())
print("path: "          + arn.get_path())
print("region: "        + arn.get_region())
print("service: "       + arn.get_service())
print("account_number: "+ arn.get_account_number())
print(arn.is_role())
print(arn.is_policy())
