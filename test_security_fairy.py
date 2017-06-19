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
# import data_collection as dc
import security_fairy_api_endpoint as sfae

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
