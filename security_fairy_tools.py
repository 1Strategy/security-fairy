import logging
import json

class InvalidArn(Exception):
    pass

class InvalidStatementAction(Exception):
    pass

class Arn:

    def __init__(self, entity_arn, logging_level = logging.INFO):
        """ Create a new point at the given coordinates. """

        logging.basicConfig(level=logging_level)

        self.full_arn           = entity_arn
        split_arn               = entity_arn.split(':')
        logging.debug(split_arn)

        if len(split_arn) != 6:
            raise InvalidArn("The given arn is invalid: {entity_arn}".format(entity_arn=entity_arn))

        self.entity_name        = ''
        self.entity_type        = ''
        self.path               = ''
        self.account_number     = split_arn[4]
        self.region             = split_arn[3]
        self.service            = split_arn[2]
        self.extract_entity(split_arn)

    def is_role(self):
        if self.entity_type == 'role':
            return True
        return False

    def is_policy(self):
        if self.entity_type == 'policy':
            return True
        return False

    def is_assumed_role(self):
        # arn:aws:iam::281782457076:assumed-role/1s_tear_down_role
        pass

    def extract_entity(self, split_arn):
        entity              = split_arn[5].split('/')
        self.entity_type    = entity[0]
        self.entity_name    = entity[len(entity)-1]
        self.path           = '' if entity[len(entity)-1]==entity[1] else entity[1]
        logging.debug(self.path)
        logging.debug(entity)

    def get_full_arn(self):
        return self.full_arn

    def get_entity_type(self):
        return self.entity_type

    def get_entity_name(self):
        return self.entity_name

    def get_path(self):
        return self.path

    def get_region(self):
        return self.region

    def get_service(self):
        return self.service

    def get_account_number(self):
        return self.account_number

class IAMPolicy:

    def __init__(self, logging_level = logging.DEBUG):
        logging.basicConfig(level=logging_level)
        self.statements = []

    def add_statement(self, statement):
        if not isinstance(statement, IAMStatement):
            raise Exception('This Method only supports objects of type IAMStatement')
        self.statements.append(statement.get_statement())

    def get_policy(self):
        policy = {
                    "Version": "2012-10-17",
                    "Statement": self.statements
                }
        logging.debug(policy)
        return policy

    def print_policy(self):
        policy = {
                    "Version": "2012-10-17",
                    "Statement": self.statements
                 }
        logging.debug(policy)
        return json.dumps(policy)


class IAMStatement:
    def __init__(self, effect, actions, resource, logging_level = logging.WARNING):
        logging.basicConfig(level=logging_level)
        self.validate_statement(effect, actions, resource)
        self.actions    = actions
        self.resource   = resource
        self.effect     = effect

    def validate_statement(self, effect, actions, resource):
        if not effect.lower() in ['allow', 'deny']:
            logging.debug(effect)
            raise InvalidStatementAction("Valid Effects are 'Allow' and 'Deny'.")

        if not resource == '*':
            logging.debug(resource)
            raise Exception('Invalid Resource.')

        logging.debug(actions)

        for action in actions:
            if len(action.split(':')) != 2:
                raise InvalidStatementAction('Invalid Statement: {action} Statement must be \'service:api-action\'.'.format(action=action))
        self.actions = actions


    def get_statement(self):
        if self.actions == []:
            raise Exception('This statement has no Actions')

        return {
            "Effect": self.effect,
            "Resource": self.resource,
            "Action": self.actions
        }


logging_level = logging.INFO
statement = IAMStatement('Allow',["pot:atosoup","goat:cheese"],'*', logging_level = logging_level)
statement.get_statement()
policy = IAMPolicy(logging_level = logging_level)
policy.add_statement(statement)
print(policy.print_policy())
print(policy.get_policy())

# arn = Arn('arn:aws:iam::281782457076:role/1s_tear_down_role', logging_level = logging.DEBUG)
# arn = Arn('arn:aws:iam:us-east-1:842337631775:role/service-role/StatesExecutionRole-us-west-2')
# print("full_arn: "      + arn.get_full_arn())
# print("entity_name: "   + arn.get_entity_name())
# print("entity_type: "   + arn.get_entity_type())
# print("path: "          + arn.get_path())
# print("region: "        + arn.get_region())
# print("service: "       + arn.get_service())
# print("account_number: "+ arn.get_account_number())
# print(arn.is_role())
# print(arn.is_policy())
