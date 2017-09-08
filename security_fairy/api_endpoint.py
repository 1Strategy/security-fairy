"""API Endpoint

Validates inputs to the Security Fairy tool,
then creates and executes the State Machine
which orchestrates the Security Fairy
Lambda functions.
"""


import json
import re
import os
import string
import boto3

from botocore.exceptions import ProfileNotFound
from security_fairy_tools import Arn

try:
    SESSION = boto3.session.Session(profile_name='training')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()



def lambda_handler(event, context):
    """
    Executed by the Lambda service.

    Returns the validated inputs and invokes
    the State Machine that orchestrates
    Security Fairy.
    """

    api_return_payload = {
        'statusCode': 500,
        'headers':{
            'Content-Type':'application/json'
        },
        'body':'Security Fairy Internal Server Error.'
    }


    domain = get_domain(event)
    method = event['httpMethod']

    if method == 'GET':
        return api_website(event, domain)

    if method == 'POST':
        return post_response(event, domain)

    return api_return_payload


def post_response(event, domain):

    api_return_payload = {
        'statusCode': 500,
        'headers':{
            'Content-Type':'application/json'
        },
        'body':'Security Fairy Internal Server Error.'
    }

    print(event)

    try:
        inputs = validate_inputs(event)
        invoke_state_machine(inputs)

        api_return_payload['statusCode'] = 200
        api_return_payload['body'] = 'Inputs are valid. You should receive an email shortly.'

    except Exception as error:
        print(error)
        api_return_payload['statusCode'] = 200
        api_return_payload['body'] = "Unsuccessful: {error}".format(error=error)

    print api_return_payload
    return api_return_payload

def get_domain(event):

    # Supports test invocations from API Gateway
    if event['headers'] is None:
        return "https://testinvocation/start"

    # Extracts the domain from event object based on for both api gateway URLs
    # or custom domains
    if 'amazonaws.com' in event['headers']['Host']:
        return "https://{domain}/{stage}{path}".format(domain=event['headers']['Host'],
                                                       stage=event['requestContext']['stage'],
                                                       path=event['path'])
    else:
        return "https://{domain}{path}".format(domain=event['headers']['Host'],
                                               path=event['path'])

def invoke_state_machine(inputs):
    """Invoke state machine"""
    print json.dumps(inputs)
    sfn_client = SESSION.client('stepfunctions')
    response = sfn_client.start_execution(stateMachineArn=os.environ['state_machine'],
                                          input=json.dumps(inputs)
                                         )
    print(response)


def validate_inputs(event):
    """Validate inputs"""
    input_payload = json.loads(event['body'])
    num_days = validate_date_window(input_payload.get('num_days', 7))
    entity_arn = validate_entity_arn(input_payload.get('entity_arn'))

    return {
        'num_days'  : num_days*-1,
        'entity_arn': entity_arn
    }


def validate_date_window(days):
    """Validate the date range for the Security Fairy query"""
    window = abs(days)
    if window > 30 or window < 1:
        print window
        raise ValueError('Valid number of days is between 1 and 30 inclusive.')

    return window


def validate_entity_arn(entity_arn):
    """Validate entity ARN"""

    # account_number = SESSION.client('sts').get_caller_identity()["Account"]
    # Roles are valid: arn:aws:iam::842337631775:role/1S-Admins
    #                  arn:aws:sts::281782457076:assumed-role/1S-Admins/alex
    # Users are invalid: arn:aws:iam::842337631775:user/aaron

    try:
        arn = Arn(entity_arn)
    except Exception:
        raise ValueError('Malformed ARN. Please enter a role ARN.')
    print(arn.entity_type)

    if 'user' in arn.entity_type:
        raise ValueError('Users not supported. Please enter a role ARN.')

    if 'group' in arn.entity_type:
        raise ValueError('Groups not supported. Please enter a role ARN.')

    if not arn.is_assumed_role() and not arn.is_role():
        raise ValueError('Invalid Resource ARN.')
    # pattern = re.compile("arn:aws:(sts|iam)::(\d{12})?:(role|assumed-role)\/(.*)")

    # if not pattern.match(entity_arn):
    #     raise ValueError('Invalid Resource ARN.')

    assumed_role_pattern = re.compile("arn:aws:sts::(\d{12})?:assumed-role\/(.*)\/(.*)")

    if not assumed_role_pattern.match(entity_arn):
        refactored_arn  = "arn:aws:sts::" + arn.get_account_number() + ":assumed-role/" + arn.get_entity_name()
        entity_arn      = refactored_arn
        SESSION.client('iam').get_role(RoleName=arn.get_entity_name())

    return entity_arn


def invoke_state_machine(inputs):
    print(json.dumps(inputs))
    response = SESSION.client('stepfunctions').start_execution( stateMachineArn=os.environ['state_machine'],
                                                                input=json.dumps(inputs))
    print(response)


def api_website(event, domain):

    body = """
    <html>
    <body bgcolor=\"#E6E6FA\">
    <head>
    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
    <style>
    .form {
        padding-left: 1cm;
    }

    .div{
      padding-left: 1cm;
    }
    </style>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
    <script>

    $(document).ready(function(){
        $("button").click(function(){
          var entity_arn = document.getElementById("entity_arn").value;
          var dict = {};
          dict["entity_arn"] = entity_arn;
          if (document.getElementById("num_days").value != "") {
              dict["num_days"] = Number(document.getElementById("num_days").value);
          }
          else{
              dict["num_days"] = 30;
          };

          $.ajax({
            type: 'POST',
            headers: {
                'Content-Type':'application/json',
                'Accept':'text/html'
            },
            url:'$domain',
            crossDomain: true,
            data: JSON.stringify(dict),
            dataType: 'text',
            success: function(responseData) {
                alert(responseData);
                //document.getElementById("id").innerHTML = responseData;
                document.getElementById("entity_arn").value="";
                document.getElementById("num_days").value="";
            },
            error: function (responseData) {
                //alert(responseData);
                alert('POST failed.'+ JSON.stringify(responseData));
            }
          });
        });
    });
    </script>
    </head>
    <title>Security Fairy IAM Policy Remediation Tool</title>
    <h1 class="div">Security Fairy IAM Remediation Tool</h1>
    <body>

      <form class="form" action="" method="post">
            <textarea rows="1" cols="50" name="text" id="entity_arn" placeholder="arn:aws:iam::0123456789:role/roleName"></textarea>
      </form>
      <form class="form" action="" method="post">
            <textarea rows="1" cols="50" name="text" id="num_days" placeholder="Scan the logs for between 1-30 days (Enter Number)"></textarea>
      </form>


    <div class="div"><button class="btn btn-primary">Audit Entity</button></div>
    <div class="div" id="id"></div>
    </body>
    </html>
    """

    return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": 'text/html',
                    "Access-Control-Allow-Origin": "*"
                },
                "body": string.Template(body).safe_substitute({"domain": domain})
    }


if __name__ == '__main__':
    print(validate_entity_arn('arn:aws:sts::842337631775:assumed-role/1S-Admins/potato'))
