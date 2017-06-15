import boto3
import json
import re
import os
import string

try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()

api_return_payload = {
    'statusCode': 500,
    'headers':{
        'Content-Type':'application/json'
    },
    'body':'Security Fairy Internal Server Error.'
}


def lambda_handler(event, context):

    # Default API Response returns an error
    domain = get_domain(event)

    if method == 'GET':
        return api_website(event, domain)

    if method == 'POST':
        return post_response(event, domain)

    return api_return_payload

def post_response(event, domain):

    try:
        inputs = validate_inputs(event)
        invoke_state_machine(inputs)

        api_return_payload['statusCode'] = 200
        api_return_payload['body'] = 'Inputs are valid.'

    except Exception as error:
        api_return_payload['statusCode'] = 500
        api_return_payload['body'] = "Unsuccessful:\n {error}".format(error=error)

    print(api_return_payload)
    return api_return_payload

def get_domain(event):

    # Supports test invocations from API Gateway
    if event['headers'] is None:
        return "https://testinvocation/start"

    # Extracts the domain from event object based on for both api gateway URLs
    # or custom domains
    if 'amazonaws.com' in event['headers']['Host']:
        return "https://{domain}/{stage}/".format(domain=event['headers']['Host'],
                                                         stage=event['requestContext']['stage'])
    else:
        return "https://{domain}/".format(domain=event['headers']['Host'])


def validate_inputs(event):
    input_payload = json.loads(event['body'])
    num_days = abs(input_payload.get('num_days', 14))
    if num_days > 30 or num_days < 1:
        print(num_days)
        raise ValueError('Valid number of days is between 1 and 30 inclusive.')


    entity_arn = validate_entity_arn(input_payload.get('entity_arn'))

    return {
        'num_days'  : num_days*-1,
        'entity_arn': entity_arn
    }

def validate_entity_arn(entity_arn):

    # account_number = session.client('sts').get_caller_identity()["Account"]
    # Roles are valid: arn:aws:iam::842337631775:role/1S-Admins
    #                  arn:aws:sts::281782457076:assumed-role/1S-Admins/alex
    # Users are invalid: arn:aws:iam::842337631775:user/aaron

    if 'user' in entity_arn:
        raise ValueError('Users not supported. Please enter a role ARN.')

    if 'group' in entity_arn:
        raise ValueError('Groups not supported. Please enter a role ARN.')

    pattern = re.compile("arn:aws:(sts|iam)::(\d{12})?:(role|assumed-role)\/(.*)")

    if not pattern.match(entity_arn):
        raise ValueError('Invalid Resource ARN.')

    assumed_role_pattern = re.compile("arn:aws:sts::(\d{12})?:assumed-role\/(.*)\/(.*)")

    if not assumed_role_pattern.match(entity_arn):

        split_arn       = re.split('/|:', entity_arn)
        refactored_arn  = "arn:aws:sts::" + split_arn[4] + ":assumed-role/" + split_arn[6]
        entity_arn      = refactored_arn
        session.client('iam').get_role(RoleName=split_arn[6])

    return entity_arn


def invoke_state_machine(inputs):
    print(json.dumps(inputs))
    response = session.client('stepfunctions').start_execution( stateMachineArn=os.environ['state_machine'],
                                                                input=json.dumps(inputs))
    print(response)


def api_website(event, domain):
    # returns a website front end for the redirect tool
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
          dict["destination_url"] = entity_arn;
          if (document.getElementById("num_days").value != "") {
              dict["custom_token"] = document.getElementById("num_days").value;
          }

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
                document.getElementById("id").innerHTML = responseData;
            },
            error: function (responseData) {
                alert('POST failed.'+ JSON.stringify(responseData));
            }
          });
        });
    });
    </script>
    </head>
    <title>Security Fairy IAM Policy Auditor</title>
    <h1 class="div">Security Fairy IAM Policy Auditor</h1>
    <body>

      <form class="form" action="" method="post">
            <textarea rows="1" cols="50" name="text" id="entity_arn" placeholder="arn:aws:iam::0123456789:role/roleName"></textarea>
      </form>
      <form class="form" action="" method="post">
            <textarea rows="1" cols="50" name="text" id="num_days" placeholder="14"></textarea>
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
