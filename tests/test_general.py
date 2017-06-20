"""Security Fairy Tests

This module tests each piece of the Security Fairy tool.
Modules that don't have tests written are in the ``Todo`` section.

Todo:
    * API approval
    * API endpoint
    * Athena Query
    * Email approval request
    * Get task token
    * Revised policy approve
    * Revised policy deny
    * Revised policy generator
    * Variable injection
    * Data collection
"""

import pytest
# import security_fairy.data_collection as dc
import security_fairy.security_fairy_api_endpoint as sfae
import security_fairy.security_fairy_api_approval as sfaa

# ML tests
# def test_role_output_type():
#     """Hello"""
#     roles = dc.list_all_roles()
#     print roles[0]
#     assert isinstance(dc.list_all_roles(), list)


# def test_inline_policies():
#     """Hello"""
#     inline_policies = dc.list_inline_policies('1S-Admins')
#     print inline_policies
#     assert isinstance(dc.list_inline_policies('1S-Admins'), list)


# def test_managed_policies():
#     """Hello"""
#     managed_policies = dc.list_managed_policies('1S-Admins')
#     print managed_policies
#     assert isinstance(dc.list_managed_policies('1S-Admins'), list)

class TestInputValidationClass(object):
    """Class for validating inputs to Security Fairy"""
    def test_input_validation_1(self):
        """CloudTrail retrieval window is too long"""
        event = {'body':
                 "{\
                   \"entity_arn\":\"arn:aws:sts::281782457076:assumed-role/1S-Admins/alex\",\
                     \"num_days\":31\
                  }"
                }
        with pytest.raises(ValueError):
            sfae.validate_inputs(event)

    def test_input_validation_2(self):
        """No account number in the ARN"""
        event = {'body':
                 "{\
                   \"entity_arn\":\"arn:aws:sts::assumed-role/1S-Admins/alex\",\
                     \"num_days\":31\
                  }"
                }
        with pytest.raises(ValueError):
            sfae.validate_inputs(event)


class TestApiApprovalClass(object):
    """Test the api_approval module"""


    def test_none_get_domain(self):
        """Test event['headers'] = None"""
        assert api_approval(
            {
                'body': '{"task_token":"AAAAKgAAAAIAAAAAAAAAAbwck0ZXLox0l5UCsjE3iQN3iBJNAu9ZWh/ElSrNKHdVP90ZxgrPZvFQZMnl+dcD4J9VdwieXvx2s6VBpQ1AsIrJLYM7y9D1bDRvrct34LA4YldibA7gw3dz5YmvScrCiLX8DLPT5BiKkpKtwN5pVXqlC0fZcSQ4Z2ZdSvAN/awy6S678p5QyxsJlqe3pQpbIZfmQ4XjboqpLMIWSMDkYajtBuxMgtfyX879s5QHzCZ9d0B29WI3FV0PS07xMYrqn+2Nu/2l64JvKMMNBknJZiM2c92AQFZMFvOvMCHnxbtLqZjZpWTaW5Z3O0Cv5B91l6T7bZvk6Dp7QZ6fAdYlQw8S/YT0Vz6z/sMPDf3bxPfGJ9b4cjVHbLX0nK4BEvlAW/OEXJGGYG9X2V/gUoRMs/RwEenzvxi5raZPsHlCqOZzmuszC1H4duNQBaRjF2vzOY60wyOoP7/shrdfPvGKh9LMMUi/ir2y9W8hbCb6R1MZERE9yOIUlK+c5NHZf64JnRvNG2tUF4efOjVIbZfLrayDEAgLqeOtlXSy7yOLxSjdmqcVKXmD2AdnLg2yi/HYyyUc3fQPZES6nPOMpuLz27E=","execution_id":"9487c326-23fc-46d6-a2c2-69b6342b5162"}',
                'headers': None,
                'httpMethod': 'POST',
                'pathParameters': {
                    'approval': 'deny'
                }
            },
            ''
            ) == {'body': '', 'headers': {'Content-Type': 'application/json'}, 'statusCode': 200}


    def test_aws_get_domain(self):
        """Test amazonaws.com in event['headers']['Host']"""
        assert api_approval(
            {
                'body': '{"task_token":"AAAAKgAAAAIAAAAAAAAAAbwck0ZXLox0l5UCsjE3iQN3iBJNAu9ZWh/ElSrNKHdVP90ZxgrPZvFQZMnl+dcD4J9VdwieXvx2s6VBpQ1AsIrJLYM7y9D1bDRvrct34LA4YldibA7gw3dz5YmvScrCiLX8DLPT5BiKkpKtwN5pVXqlC0fZcSQ4Z2ZdSvAN/awy6S678p5QyxsJlqe3pQpbIZfmQ4XjboqpLMIWSMDkYajtBuxMgtfyX879s5QHzCZ9d0B29WI3FV0PS07xMYrqn+2Nu/2l64JvKMMNBknJZiM2c92AQFZMFvOvMCHnxbtLqZjZpWTaW5Z3O0Cv5B91l6T7bZvk6Dp7QZ6fAdYlQw8S/YT0Vz6z/sMPDf3bxPfGJ9b4cjVHbLX0nK4BEvlAW/OEXJGGYG9X2V/gUoRMs/RwEenzvxi5raZPsHlCqOZzmuszC1H4duNQBaRjF2vzOY60wyOoP7/shrdfPvGKh9LMMUi/ir2y9W8hbCb6R1MZERE9yOIUlK+c5NHZf64JnRvNG2tUF4efOjVIbZfLrayDEAgLqeOtlXSy7yOLxSjdmqcVKXmD2AdnLg2yi/HYyyUc3fQPZES6nPOMpuLz27E=","execution_id":"9487c326-23fc-46d6-a2c2-69b6342b5162"}',
                'headers': {'Host': 'ezwzmmh526.execute-api.us-east-1.amazonaws.com'},
                'requestContext': {'stage': 'Prod'},
                'httpMethod': 'POST',
                'pathParameters': {
                    'approval': 'deny'
                }
            },
            ''
            ) == {'body': '', 'headers': {'Content-Type': 'application/json'}, 'statusCode': 200}


    def test_get_domain(self):
        """No amazonaws.com in event['headers']['Host']"""
        assert api_approval(
            {
                'body': '{"task_token":"AAAAKgAAAAIAAAAAAAAAAbwck0ZXLox0l5UCsjE3iQN3iBJNAu9ZWh/ElSrNKHdVP90ZxgrPZvFQZMnl+dcD4J9VdwieXvx2s6VBpQ1AsIrJLYM7y9D1bDRvrct34LA4YldibA7gw3dz5YmvScrCiLX8DLPT5BiKkpKtwN5pVXqlC0fZcSQ4Z2ZdSvAN/awy6S678p5QyxsJlqe3pQpbIZfmQ4XjboqpLMIWSMDkYajtBuxMgtfyX879s5QHzCZ9d0B29WI3FV0PS07xMYrqn+2Nu/2l64JvKMMNBknJZiM2c92AQFZMFvOvMCHnxbtLqZjZpWTaW5Z3O0Cv5B91l6T7bZvk6Dp7QZ6fAdYlQw8S/YT0Vz6z/sMPDf3bxPfGJ9b4cjVHbLX0nK4BEvlAW/OEXJGGYG9X2V/gUoRMs/RwEenzvxi5raZPsHlCqOZzmuszC1H4duNQBaRjF2vzOY60wyOoP7/shrdfPvGKh9LMMUi/ir2y9W8hbCb6R1MZERE9yOIUlK+c5NHZf64JnRvNG2tUF4efOjVIbZfLrayDEAgLqeOtlXSy7yOLxSjdmqcVKXmD2AdnLg2yi/HYyyUc3fQPZES6nPOMpuLz27E=","execution_id":"9487c326-23fc-46d6-a2c2-69b6342b5162"}',
                'headers': {'Host': 'ezwzmmh526.execute-api.us-east-1.amazonaws.com'},
                'requestContext': {'stage': 'Prod'},
                'httpMethod': 'POST',
                'pathParameters': {
                    'approval': 'deny'
                }
            },
            ''
            ) == {'body': '', 'headers': {'Content-Type': 'application/json'}, 'statusCode': 200}
