"""Security Fairy Tests

This module tests each piece of the Security Fairy tool.
Modules that don't have tests written are in the ``Todo`` section.

Todo:
    * API approval
        + Dependency injection:
            - test_task_token_*()
            - test_api_website_*()
    * API endpoint
        + Dependency Injection
            - test_invoke_state_machine_*()
    * Athena Query
    * Revised policy approve
    * Revised policy deny
    * Revised policy generator
    * Variable injection
    * Data collection
"""


import pytest
import security_fairy.security_fairy_api_approval as sfaa
import security_fairy.security_fairy_api_endpoint as sfae
import security_fairy.security_fairy_athena_query as sfaq
import security_fairy.security_fairy_revised_policy_approve as sfrpa
import security_fairy.security_fairy_revised_policy_generator as sfrpg


class TestApiApprovalClass(object):
    """Test the api_approval module"""


    def test_none_get_domain(self):
        """Test event['headers'] = None
        Should return the default domain name of testinvocation
        """
        assert sfaa.get_domain({'headers': None}) == 'https://testinvocation/approve'


    def test_aws_get_domain(self):
        """Test 'amazonaws.com' in event['headers']['Host']
        Should return the amazonaws.com domain with the correct requestContext
        """
        assert sfaa.get_domain(
            {
                'headers': {
                    'Host': 'ezwzmmh526.execute-api.us-east-1.amazonaws.com'
                },
                'requestContext': {
                    'stage': 'Prod'
                }
            }
        ) == 'https://ezwzmmh526.execute-api.us-east-1.amazonaws.com/Prod/'


    def test_get_domain(self):
        """No amazonaws.com in event['headers']['Host']
        Should return the correct domain in the headers stanza
        """
        assert sfaa.get_domain(
            {
                'headers': {
                    'Host': 'ezwzmmh526.execute-api.us-east-1.blah-blah.test'
                }
            }
        ) == 'https://ezwzmmh526.execute-api.us-east-1.blah-blah.test/'


    def test_token_task_approve(self):
        """Test 'approve' in event[pathParameters]['approval']
        Should return json payload with 'body' = 'New policy applied'
        """
        assert sfaa.token_task(
            {
                'pathParameters': {
                    'approval': 'approve'
                },
                'body': '{"task_token":"AAAAKgAAAAIAAAAAAAAAAbwck0ZXLox0l5UCsjE3iQN3iBJNAu9ZWh/ElSrNKHdVP90ZxgrPZvFQZMnl+dcD4J9VdwieXvx2s6VBpQ1AsIrJLYM7y9D1bDRvrct34LA4YldibA7gw3dz5YmvScrCiLX8DLPT5BiKkpKtwN5pVXqlC0fZcSQ4Z2ZdSvAN/awy6S678p5QyxsJlqe3pQpbIZfmQ4XjboqpLMIWSMDkYajtBuxMgtfyX879s5QHzCZ9d0B29WI3FV0PS07xMYrqn+2Nu/2l64JvKMMNBknJZiM2c92AQFZMFvOvMCHnxbtLqZjZpWTaW5Z3O0Cv5B91l6T7bZvk6Dp7QZ6fAdYlQw8S/YT0Vz6z/sMPDf3bxPfGJ9b4cjVHbLX0nK4BEvlAW/OEXJGGYG9X2V/gUoRMs/RwEenzvxi5raZPsHlCqOZzmuszC1H4duNQBaRjF2vzOY60wyOoP7/shrdfPvGKh9LMMUi/ir2y9W8hbCb6R1MZERE9yOIUlK+c5NHZf64JnRvNG2tUF4efOjVIbZfLrayDEAgLqeOtlXSy7yOLxSjdmqcVKXmD2AdnLg2yi/HYyyUc3fQPZES6nPOMpuLz27E=","execution_id":"9487c326-23fc-46d6-a2c2-69b6342b5162"}'
            }
        ) == {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': 'New policy applied.'
            }


    def test_token_task_deny(self):
        """Test 'deny' in event[pathParameters]['approval']
        Should return json payload with 'body' = 'Revised Policy deleted.'
        """
        assert sfaa.token_task(
            {
                'pathParameters': {
                    'approval': 'deny'
                },
                'body': '{"task_token":"AAAAKgAAAAIAAAAAAAAAAbwck0ZXLox0l5UCsjE3iQN3iBJNAu9ZWh/ElSrNKHdVP90ZxgrPZvFQZMnl+dcD4J9VdwieXvx2s6VBpQ1AsIrJLYM7y9D1bDRvrct34LA4YldibA7gw3dz5YmvScrCiLX8DLPT5BiKkpKtwN5pVXqlC0fZcSQ4Z2ZdSvAN/awy6S678p5QyxsJlqe3pQpbIZfmQ4XjboqpLMIWSMDkYajtBuxMgtfyX879s5QHzCZ9d0B29WI3FV0PS07xMYrqn+2Nu/2l64JvKMMNBknJZiM2c92AQFZMFvOvMCHnxbtLqZjZpWTaW5Z3O0Cv5B91l6T7bZvk6Dp7QZ6fAdYlQw8S/YT0Vz6z/sMPDf3bxPfGJ9b4cjVHbLX0nK4BEvlAW/OEXJGGYG9X2V/gUoRMs/RwEenzvxi5raZPsHlCqOZzmuszC1H4duNQBaRjF2vzOY60wyOoP7/shrdfPvGKh9LMMUi/ir2y9W8hbCb6R1MZERE9yOIUlK+c5NHZf64JnRvNG2tUF4efOjVIbZfLrayDEAgLqeOtlXSy7yOLxSjdmqcVKXmD2AdnLg2yi/HYyyUc3fQPZES6nPOMpuLz27E=","execution_id":"9487c326-23fc-46d6-a2c2-69b6342b5162"}'
            }
        ) == {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': 'Revised Policy deleted.'
            }


    def test_api_website(self):
        """Test api website"""
        assert sfaa.api_website({'queryStringParameters': None}) == "something"


class TestApiEndpointClass(object):
    """Class for validating inputs to Security Fairy"""


    # def test_invoke_state_machine(self):
    #     """Test invocation of the state machine"""
    #     assert Hello


    def test_validate_inputs(self):
        """Test num_days < 30 and valid entity_arn
        Should return a json object with correct date window and arn
        """
        assert sfae.validate_inputs(
            {
                'body': "{\
                    \"entity_arn\":\"arn:aws:sts::281782457076:assumed-role/1S-Admins/alex\",\
                    \"num_days\":20\
                }"
            }
        ) == {
            'num_days'  : -20,
            'entity_arn': 'arn:aws:sts::281782457076:assumed-role/1S-Admins/alex'
            }


    def test_validate_inputs_big_window(self):
        """Test num_days > 30
        Should raise an invalid date range error
        """
        event = {'body': "{\
                    \"entity_arn\":\"arn:aws:sts::281782457076:assumed-role/1S-Admins/alex\",\
                    \"num_days\":31\
                    }"
                }
        with pytest.raises(ValueError):
            sfae.validate_inputs(event)


    def test_validate_inputs_bad_arn(self):
        """Test for invalid ARN in event['body']
        Should raise an invalid ARN error
        """
        event = {'body':
                 "{\
                   \"entity_arn\":\"arn:aws:sts::assumed-role/1S-Admins/alex\",\
                     \"num_days\":31\
                  }"
                }
        with pytest.raises(ValueError):
            sfae.validate_inputs(event)


class TestAthenaQueryClass(object):
    """Class for Athena Query tests"""


    def test_execute_query(self):
        """Test query execution"""
        assert sfaq.execute_query(
            "arn:aws:iam::281782457076:assumed-role/1s_tear_down_role",
            "-30",
            "1s-potato-east"
            ) == ''


class TestRevisedPolicyApprove(object):
    """Class for Revised Policy Approve tests"""


    def test_get_revised_policy(self):
        """Test get revised policy"""
        assert sfrpa.get_revised_policy('') == ''


    def test_get_entity_name_from_arn(self):
        """Test get entity name from arn"""
        arn = 'arn:aws:iam::281782457076:role/1s_security_fairy_role'
        assert sfrpa.get_entity_name_from_arn(arn) == 'role'


class TestRevisedPolicyGenerator(object):
    """Class for Revised Policy Generator"""


    def test_get_permissions_from_query(self):
        """test get permissions from query function"""
        result_set = [{'VarCharValue': 'ServiceA.amazonaws.com'},
                      {'VarCharValue': '[testActionOne, testActionTwo]'}
                     ]
        assert sfrpg.get_permissions_from_query(result_set) == ""


    def test_build_policy_from_query_actions(self):
        """test build policy from query actions"""
        assert sfrpg.build_policy_from_query_actions('') == ''
