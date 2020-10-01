
import logging
import json
import re
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
            # Checks for extraneous lambda api version information:
            # e.g.  lambda:ListTags20170331
            #       lambda:GetFunctionConfiguration20150331v2"
            #       lambda:"UpdateFunctionCode20150331v2"

            api_version_info = re.findall(r"(\d+v\d+)|(\d+)", split_statement_action[1])
            if api_version_info:
                for api_version in api_version_info[0]:
                    logging.debug(api_version)
                    if api_version is not '':
                        action = split_statement_action[1].replace(api_version,'')
            else:
                action = split_statement_action[1]
        else:
            action = split_statement_action[1]

        logging.debug(statement_action)
        logging.debug(self.service_actions.get(service))

        if self.service_actions.get(service) is None:
            self.service_actions[service] = []

        if not action in self.service_actions[service]:
            self.service_actions[service].append(action)
            logging.debug("Action added: {service}:{action}".format(service=service, action=action))

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
                                            sid='SecurityFairyBuilt{service}Policy'.format(service=service.capitalize())
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
