import string
import boto3
import json
import re
import os

try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()


def lambda_handler(event, context):

    api_response = {
      "statusCode": 500,
      "headers":{
          "Content-Type":"application/json"
      },
      "body":"Interal Server Error"
    }

    print(event)

    method = event['httpMethod']
    domain = get_domain(event)

    if method == 'GET':# and event['queryStringParameters'] is not None:
        return api_website(event, domain)

    if method == 'POST':
        return return_step_function_token_task(event, domain)

    # Default API Response returns an error
    return api_response


def get_domain(event):

    # Supports test invocations from API Gateway
    if event['headers'] is None:
        return "https://testinvocation/approve"

    # Extracts the domain from event object based on for both api gateway URLs
    # or custom domains
    if 'amazonaws.com' in event['headers']['Host']:
        return "https://{domain}/{stage}/".format(domain=event['headers']['Host'],
                                                         stage=event['requestContext']['stage'])
    else:
        return "https://{domain}/".format(domain=event['headers']['Host'])


def return_step_function_token_task(event, domain):

    sfn_client = session.client('stepfunctions')
    approval = event["pathParameters"].get("approval", "deny")

    print(approval)
    print(json.loads(event['body']))

    if approval is 'approve':
        sfn_client.send_task_success(taskToken=event['queryStringParameters']['task-token'],
                                     output="{}")
    if approval is 'deny':
        sfn_client.send_task_failure(taskToken=event['queryStringParameters']['task-token'],
                                     output="{}")

    return {
        "statusCode":200,
        "headers":{},
        "body": approval
    }


def api_website(event, domain):
    # returns a website front end for approval
    dynamodb_client = session.client('dynamodb')

    try:
        dynamodb_id = event['queryStringParameters']['id']
        new_policy = dynamodb_client.get_item(TableName=os.environ['dynamodb_table'],
                                          Key={'execution_id': {'S': "{}".format(dynamodb_key)}})['Item']['new_policy']['S']
    except Exception:
        new_policy = {"Error": "This Exection Id has either expired or is invalid."}

    body = """
            <html>
            <body bgcolor=\"#E6E6FA\">
            <head>
            <!-- Latest compiled and minified CSS -->
            <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
            <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
            <style>
            .code {
                max-height: 500px;
                width: 600px;
                overflow: scroll;
                text-align: left;
                margin-bottom: 20px;
            }
            </style>
            <script>
            function getUrlParameter(name) {
                name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
                var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
                var results = regex.exec(location.search);
                return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
            };

            var dict = {};
            var taskToken = getUrlParameter('task-token');
            var executionId = getUrlParameter('execution_id');
            dict['task-token']= taskToken;
            dict['execution_id']=executionId;

          function submitRequest(approval){

            $.ajax({
              type: 'POST',
              headers: {
                  'Content-Type':'application/json',
                  'Accept':'text/html'
              },
              url:'$domain'+approval,
              crossDomain: true,
              data: JSON.stringify(dict),
              dataType: 'text',
              success: function(responseData) {
                  document.getElementById("output").innerHTML = responseData;
              },
              error: function (responseData) {
                  alert('POST failed.'+ JSON.stringify(responseData));
              }
            });
            };

            $(document).ready(function(){

                document.getElementById("output").innerHTML = JSON.stringify($new_policy, null, "\\t");
                $("#approve").click(function(){
                  console.log("Approve button clicked");
                  submitRequest("approve");
                });
                $("#deny").click(function(){
                  console.log("deny button clicked");
                  submitRequest("deny");
                });
            });

            </script>
            </head>
            <body>
            <center>
            <title>IAM Security Fairy</title>
            <h1><span class="glyphicon glyphicon-fire text-danger" ></span> IAM Security Fairy</h1>

            <div class="code"><pre id='output'></pre></div>
            <button class="btn btn-primary" id='approve'>Approve</button>
            <button class="btn btn-danger" id='deny'>Deny</button>
            </center>
            </body>
            </html>"""

    replace_dict = dict(new_policy=new_policy, domain=domain)
    string.Template(body).safe_substitute(replace_dict)

    return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "text/html",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": string.Template(body).safe_substitute(replace_dict)
    }






if __name__ == '__main__':
    event = {
  "body": "{\"execution_id\":\"some-key\"}",
  "resource": "/{proxy+}",
  "requestContext": {
    "resourceId": "123456",
    "apiId": "1234567890",
    "resourcePath": "/{proxy+}",
    "identity": {
    },
    "stage": "prod"
  },
  "queryStringParameters": {
    "task-token": "some-guid-i-get",
    "execution_id":"some-other-guid",
  },
  "headers": {
    "Accept-Language": "en-US,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Upgrade-Insecure-Requests": "1",
    "X-Forwarded-Port": "443",
    "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
    "X-Forwarded-Proto": "https",
    "User-Agent": "Custom User Agent String",
    "CloudFront-Forwarded-Proto": "https"
  },
  "pathParameters": {
    "proxy": "approve"
  },
  "httpMethod": "POST",
  "path": "/path/to/resource"
}


    print(lambda_handler(event, {}))
