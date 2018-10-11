"""Security Fairy Lambda Handler Tests

This module tests the Lambda functionality of the Security Fairy tool.
Lambda Handlers that don't have tests written are in the ``Todo`` section.

Todo:
    * API Approval
        + Dependency Injection
            - test_api_approval_*()
    * API Endpoint
    * Athena Query
    * Email approval request
    * Get task token
    * Revised policy approve
    * Revised policy deny
    * Revised policy generator
    * Variable injection
    * Data collection
"""
import sys
sys.path.insert(0,'..')
import pytest
from api_approval import lambda_handler as api_approval
from api_endpoint import lambda_handler as api_endpoint
from athena_query import lambda_handler as athena_query
from email_approval_request import lambda_handler as email_approval_request
from get_task_token import lambda_handler as get_task_token
from revised_policy_approve import lambda_handler as revised_policy_approve
from revised_policy_deny import lambda_handler as revised_policy_deny
from revised_policy_generator import lambda_handler as revised_policy_generator
from variable_injection import lambda_handler as variable_injection


class TestLambdaHandlers(object):
    """Test the Lambda Handler from each module"""

    def test_api_approval_error(self):
        """Test Lambda Handler for api approval"""
        assert api_approval(
            {
                'httpMethod': 'POST',
                'headers': {
                    'Host': 'ezwzmmh526.execute-api.us-east-1.amazonaws.com'
                },
                'requestContext': {
                    'stage': 'Prod'},
                'pathParameters': {
                    'approval': 'deny'},
                'body': '{"task_token":"AAAAKgAAAAIAAAAAAAAAAbwck0ZXLox0l5UCsjE3iQN3iBJNAu9ZWh/ElSrNKHdVP90ZxgrPZvFQZMnl+dcD4J9VdwieXvx2s6VBpQ1AsIrJLYM7y9D1bDRvrct34LA4YldibA7gw3dz5YmvScrCiLX8DLPT5BiKkpKtwN5pVXqlC0fZcSQ4Z2ZdSvAN/awy6S678p5QyxsJlqe3pQpbIZfmQ4XjboqpLMIWSMDkYajtBuxMgtfyX879s5QHzCZ9d0B29WI3FV0PS07xMYrqn+2Nu/2l64JvKMMNBknJZiM2c92AQFZMFvOvMCHnxbtLqZjZpWTaW5Z3O0Cv5B91l6T7bZvk6Dp7QZ6fAdYlQw8S/YT0Vz6z/sMPDf3bxPfGJ9b4cjVHbLX0nK4BEvlAW/OEXJGGYG9X2V/gUoRMs/RwEenzvxi5raZPsHlCqOZzmuszC1H4duNQBaRjF2vzOY60wyOoP7/shrdfPvGKh9LMMUi/ir2y9W8hbCb6R1MZERE9yOIUlK+c5NHZf64JnRvNG2tUF4efOjVIbZfLrayDEAgLqeOtlXSy7yOLxSjdmqcVKXmD2AdnLg2yi/HYyyUc3fQPZES6nPOMpuLz27E=",\
                          "execution_id":"9487c326-23fc-46d6-a2c2-69b6342b5162"}'},
            '') == {
                "statusCode": 200,
                "headers": {
                    "Content-Type":"application/json"},
                "body": ""
                }


    def test_api_endpoint_invoke_error(self):
        """Test Default API response
        Should return 'Unsuccessful: state_machine' as the default response
        """
        assert api_endpoint(
            {
                'body': "{\"entity_arn\":\"arn:aws:sts::281782457076:role/1S-Admins\",\
                          \"num_days\":30}"
            },
            {}
            ) == {
                'body': "Unsuccessful:\n 'state_machine'",
                'headers': {
                    'Content-Type': 'application/json'
                },
                'statusCode': 500
                }


    def test_athena_query(self):
        """Test Athena Query"""
        assert athena_query({}, {}) == ""


    def test_email_approval_request(self):
        """Test email approval request"""
        assert email_approval_request({}, {}) == ""


    def test_get_task_token(self):
        """Test get task token"""
        assert get_task_token({}, {}) == ""


    def test_revised_policy_approve(self):
        """Test revised policy approve"""
        assert revised_policy_approve({}, {}) == ""


    def test_revised_policy_deny(self):
        """Test revised policy approve"""
        assert revised_policy_deny({}, {}) == ""


    def test_revised_policy_generator(self):
        """Test revised policy approve"""
        with pytest.raises(ValueError):
            revised_policy_generator({'execution_id': None}, {})


    def test_variable_injection(self):
        """Test variable injection"""
        assert variable_injection({}, {}) == ''
