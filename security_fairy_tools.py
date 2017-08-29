import logging
import json

class InvalidArn(Exception):
    pass

class InvalidStatementAction(Exception):
    pass

class Arn:

    def __init__(self, entity_arn, logging_level = logging.INFO):
        """
        This class consumes a string and validates that it is a valid
        Amazon Resource Name entity.
        """

        logging.basicConfig(level=logging_level)

        split_arn               = entity_arn.split(':')
        logging.debug(split_arn)

        if len(split_arn) != 6:
            # Throw an error if the string and resultant list don't contain
            # the 6 sections colon delimited
            # e.g. arn:aws:iam::123456789012:role/service-role/StatesExecutionRole-us-west-2
            raise InvalidArn("The given arn is invalid: {entity_arn}".format(entity_arn=entity_arn))

        self.full_arn           = entity_arn
        self.entity_name        = ''
        self.entity_type        = ''
        self.path               = ''
        self.assuming_entity    = ''
        self.account_number     = split_arn[4]
        self.region             = split_arn[3]
        self.service            = split_arn[2]
        self.extract_entity(split_arn)

    def extract_entity(self, split_arn):
        entity              = split_arn[5].split('/')

        logging.debug('Entity:')
        logging.debug(entity)

        if entity[0] == 'role' or 'policy':
            logging.debug("this entity is a {entity}".format(entity=entity))
            self.entity_type    = entity[0]
            self.entity_name    = entity[len(entity)-1]
            self.path           = '' if entity[len(entity)-1]==entity[1] else entity[1]
            logging.debug('Path:')
            logging.debug(self.path)
        elif entity[0] =='assumed-role':
                logging.debug("this entity is an assumed-role")
                self.entity_type    = entity[0]
                self.entity_name    = entity[1]
                self.assuming_entity = entity[2]
        else:
            self.entity_type    = entity[0]
            self.entity_name    = entity[1]

    def is_role(self):
        if self.entity_type == 'role':
            return True
        return False

    def is_policy(self):
        if self.entity_type == 'policy':
            return True
        return False

    def is_assumed_role(self):
        if self.entity_type == 'assumed-role' and self.service == 'sts':
            return True
        return False

    def convert_assumed_role_to_role(self):
        if not self.is_assumed_role():
            logging.info('ARN is not assumed-role. No action taken')
        self.full_arn = self.full_arn.replace(':sts:', ':iam:')
        self.full_arn = self.full_arn.replace(':assumed-role/',':role/')
        logging.info(self.full_arn)

        logging.info('assumed-role converted to role')


    def __rebuild_full_arn__(self):
        pass

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
        self.statements         = []
        self.service_actions    = {}
        self.max_policy_size    = {
            'user' : 2048,    # User policy size cannot exceed 2,048 characters
            'role' : 10240,   # Role policy size cannot exceed 10,240 characters
            'group': 5120    # Group policy size cannot exceed 5,120 characters
        }

    def __add_statement__(self, statement):
        if not isinstance(statement, IAMStatement):
            raise Exception('This Method only supports objects of type IAMStatement')
        self.statements.append(statement)

    def add_actions(self, statement_actions):
        for statement_action in statement_actions:
            self.add_action(statement_action)

    def add_action(self, statement_action):

        split_statement_action = statement_action.split(':')

        if len(split_statement_action) != 2:
            raise InvalidStatementAction('Invalid Statement: {action} Statement must be \'service:api-action\'.'.format(action=action))

        service = self.__get_service_alias__(split_statement_action[0])

        if service == 'lambda':
            action = ''.join([i for i in split_statement_action[1] if not i.isdigit()])
        else:
            action = split_statement_action[1]

        logging.debug(statement_action)
        logging.debug(self.service_actions.get(service))

        if self.service_actions.get(service) is None:
            self.service_actions[service] = []

        self.service_actions[service].append(action)

    def __get_service_alias__(self, service):
        service_aliases = {
            "monitoring": "cloudwatch"
        }
        return service_aliases.get(service, service)

    def __build_statements__(self):

        for service in self.service_actions:
            actions_per_service = []
            for action in self.service_actions[service]:
                actions_per_service.append(service+":"+action)
                statement = IAMStatement(   effect="Allow",
                                            actions=actions_per_service,
                                            resource="*",
                                            sid='SecurityFairy{service}Policy'.format(service=service.capitalize())
                                        )
            self.__add_statement__(statement)

    def get_policy(self):
        self.__build_statements__()
        built_policy_statements = []
        for statement in self.statements:
            built_policy_statements.append(statement.get_statement())
        policy = {
                    "Version": "2012-10-17",
                    "Statement": built_policy_statements
                }
        logging.debug(policy)
        return policy

    def print_policy(self):
        return json.dumps(self.get_policy())

class IAMStatement:
    def __init__(self, effect, actions, resource, sid='', logging_level = logging.DEBUG):
        logging.basicConfig(level=logging_level)
        self.validate_statement(effect, actions, resource)
        self.actions    = actions
        self.resource   = resource
        self.effect     = effect
        if sid != '':
            self.sid    = sid

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

        statement = {
            "Effect": self.effect,
            "Resource": self.resource,
            "Action": self.actions
        }
        if self.sid != '':
            statement['Sid'] = self.sid

        return statement
