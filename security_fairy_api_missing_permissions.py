"""API Approval

Presents the revised policy created by Security Fairy,
and waits for the user to Approve or Cancel the policy
change.
"""

from __future__ import print_function
import string
import json
import boto3
from requests.utils import unquote
from botocore.exceptions import ProfileNotFound


try:
    SESSION = boto3.session.Session(profile_name='training',
                                    region_name='us-east-1')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


def lambda_handler(event, context):
    """ Executed by the Lambda service.

    Returns the API website for users who are at the Approve
    or Cancel stage of the Security Fairy tool.
    """

    method = event['httpMethod']
    domain = get_domain(event)

    if method == 'GET':# and event['queryStringParameters'] is not None:
        return api_website(event, domain)

    # Default API Response returns an error
    return {
        "statusCode": 500,
        "headers":{
            "Content-Type":"application/json"
        },
        "body":"Something Broke"
    }


def get_domain(event):
    """Return the domain that will display the new policy."""

    if event['headers'] is None:
        return "https://testinvocation/approve"

    if 'amazonaws.com' in event['headers']['Host']:
        return "https://{domain}/{stage}/".format(  domain=event['headers']['Host'],
                                                    stage=event['requestContext']['stage'])
    else:
        return "https://{domain}/".format(domain=event['headers']['Host'])


def api_website(event, domain):
    """Displays a front end website for Approval or Cancel by the user."""
    dynamodb_client = SESSION.client('dynamodb')
    entity_arn  = ''
    entity_name = ''

    dynamodb_client = SESSION.client('dynamodb')
    try:
        execution_id = event['queryStringParameters']['execution-id']
        print(execution_id)
        response_item   = dynamodb_client.get_item( TableName=os.environ['dynamodb_table'],
                                                    Key={
                                                        "execution_id": {
                                                            "S": "{execution_id}".format(execution_id=execution_id)
                                                        }
                                                    })['Item']
        missing_permissions  = response_item['missing_permissions']['S']
        entity_arn  = response_item['entity_arn']['S']
        entity_name = entity_arn.split('/')[1]
        print(response_item)

    except Exception as error:
        print(error)
        new_policy = {"Error": "This executionId has either expired or is invalid."}

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
            var executionId = getUrlParameter('execution-id');
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
                  alert('POST failed: '+ JSON.stringify(responseData));
              }
            });

            };

            function redirect(){
                var url = "https://console.aws.amazon.com/iam/home?region=us-east-1#/roles/$entity_name";
                document.location.href = url;
            };

            $(document).ready(function(){

                document.getElementById("output").innerHTML = JSON.stringify($missing_permissions, null, "\\t");
                $("#approve").click(function(){
                  console.log("Approve button clicked");
                  submitRequest("approve");
                  setTimeout(redirect,2000);
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
            <h2></h2>
            <div class="code"><pre>$entity_arn</pre></div>
            <div class="code"><pre id='output'></pre></div>
            <button class="btn btn-primary" id='approve'>Apply</button>
            <button class="btn btn-danger" id='deny'>Cancel</button>
            </center>
            </body>
            </html>"""

    replace_dict = dict(missing_permissions=missing_permissions, domain=domain, entity_arn=entity_arn, entity_name=entity_name)
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
    EVENT = { }
    lambda_handler(EVENT, {})
