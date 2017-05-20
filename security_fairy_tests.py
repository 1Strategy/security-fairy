import security_fairy_api_endpoint
import pytest

def test_input_validation_1():
    event = {'body': "{\"entity_arn\":\"arn:aws:sts::281782457076:assumed-role/1S-Admins/alex\",\"num_days\":31}"}

    with pytest.raises(ValueError):
         security_fairy_api_endpoint.validate_inputs(event)

def test_input_validation_2():
    event = {'body': "{\"entity_arn\":\"arn:aws:sts::assumed-role/1S-Admins/alex\",\"num_days\":31}"}

    with pytest.raises(ValueError):
         security_fairy_api_endpoint.validate_inputs(event)

# def test_input_validation_3():
#     assert f() == 4
