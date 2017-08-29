"""
API Approval

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

    api_response = {
        "statusCode": 500,
        "headers":{
            "Content-Type":"application/json"
        },
        "body":"Interal Server Error"
    }
    method = event['httpMethod']
    domain = get_domain(event)

    if method == 'GET':# and event['queryStringParameters'] is not None:
        return api_website(event, domain)

    if method == 'POST':
        return token_task(event)

    # Default API Response returns an error
    return api_response


def get_domain(event):
    """Return the domain that will display the new policy."""

    if event['headers'] is None:
        return "https://testinvocation/approve"

    if 'amazonaws.com' in event['headers']['Host']:
        return "https://{domain}/{stage}/".format(  domain=event['headers']['Host'],
                                                    stage=event['requestContext']['stage'])
    else:
        return "https://{domain}/".format(domain=event['headers']['Host'])


def token_task(event):
    """Return the Step Function token task."""

    sfn_client = SESSION.client('stepfunctions')
    approved_or_denied = event["pathParameters"].get("approval", "deny")
    body = json.loads(event['body'])
    task_token = unquote(body['task_token'])
    response_string = ''

    try:
        if 'approve' in approved_or_denied:
            print('approved')
            response = sfn_client.send_task_success(taskToken=task_token,
                                                    output=json.dumps(body))
            print(response)
            response_string = "New policy applied."

        if 'deny' in approved_or_denied:
            response = sfn_client.send_task_failure(taskToken=task_token,
                                                    error='User Denial',
                                                    cause=json.dumps(body))
            response_string = "Revised Policy deleted."

    except Exception as e:
        print(e)

    return {
        "statusCode":200,
        "headers":{
            "Content-Type": "application/json"
        },
        "body": response_string
    }


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
        new_policy  = response_item['new_policy']['S']
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
            var taskToken = getUrlParameter('task-token');
            var executionId = getUrlParameter('execution-id');
            dict['task_token']= taskToken;
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

                document.getElementById("output").innerHTML = JSON.stringify($new_policy, null, "\\t");
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
            <div class="code"><pre>$entity_arn</pre></div>
            <div class="code"><pre id='output'></pre></div>
            <button class="btn btn-primary" id='approve'>Apply</button>
            <button class="btn btn-danger" id='deny'>Cancel</button>
            </center>
            </body>
            </html>"""

    replace_dict = dict(new_policy=new_policy, domain=domain, entity_arn=entity_arn, entity_name=entity_name)
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
    EVENT = {
        u'body': u'{"task_token":"AAAAKgAAAAIAAAAAAAAAAbwck0ZXLox0l5UCsjE3iQN3iBJNAu9ZWh/ElSrNKHdVP90ZxgrPZvFQZMnl+dcD4J9VdwieXvx2s6VBpQ1AsIrJLYM7y9D1bDRvrct34LA4YldibA7gw3dz5YmvScrCiLX8DLPT5BiKkpKtwN5pVXqlC0fZcSQ4Z2ZdSvAN/awy6S678p5QyxsJlqe3pQpbIZfmQ4XjboqpLMIWSMDkYajtBuxMgtfyX879s5QHzCZ9d0B29WI3FV0PS07xMYrqn+2Nu/2l64JvKMMNBknJZiM2c92AQFZMFvOvMCHnxbtLqZjZpWTaW5Z3O0Cv5B91l6T7bZvk6Dp7QZ6fAdYlQw8S/YT0Vz6z/sMPDf3bxPfGJ9b4cjVHbLX0nK4BEvlAW/OEXJGGYG9X2V/gUoRMs/RwEenzvxi5raZPsHlCqOZzmuszC1H4duNQBaRjF2vzOY60wyOoP7/shrdfPvGKh9LMMUi/ir2y9W8hbCb6R1MZERE9yOIUlK+c5NHZf64JnRvNG2tUF4efOjVIbZfLrayDEAgLqeOtlXSy7yOLxSjdmqcVKXmD2AdnLg2yi/HYyyUc3fQPZES6nPOMpuLz27E=","execution_id":"9487c326-23fc-46d6-a2c2-69b6342b5162"}',
        u'resource': u'/{approval}',
        u'requestContext': {
            u'resourceId': u'ktk3jq',
            u'apiId': u'ezwzmmh526',
            u'resourcePath': u'/{approval}',
            u'httpMethod': u'POST',
            u'requestId': u'2938ad50-50a7-11e7-bff1-93579d44e732',
            u'path': u'/Prod/deny',
            u'accountId': u'281782457076',
            u'identity': {
                u'apiKey': u'',
                u'userArn': None,
                u'cognitoAuthenticationType': None,
                u'accessKey': None,
                u'caller': None,
                u'userAgent': u'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
                u'user': None,
                u'cognitoIdentityPoolId': None,
                u'cognitoIdentityId': None,
                u'cognitoAuthenticationProvider': None,
                u'sourceIp': u'71.219.116.20',
                u'accountId': None
            },
            u'stage': u'Prod'
        },
        u'queryStringParameters': None,
        u'httpMethod': u'POST',
        u'pathParameters': {
            u'approval': u'deny'
        },
        u'headers': {
            u'origin': u'https://ezwzmmh526.execute-api.us-east-1.amazonaws.com',
            u'Via': u'2.0 3c6cd3705576f791e49d58b73a16e8f0.cloudfront.net (CloudFront)',
            u'Accept-Language': u'en-US,en;q=0.8',
            u'Accept-Encoding': u'gzip, deflate, br',
            u'CloudFront-Is-SmartTV-Viewer': u'false',
            u'CloudFront-Forwarded-Proto': u'https',
            u'X-Forwarded-For': u'71.219.116.20, 216.137.42.62',
            u'CloudFront-Viewer-Country': u'US',
            u'Accept': u'text/html',
            u'User-Agent': u'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            u'X-Amzn-Trace-Id': u'Root=1-59409bf5-31a996a67ad3927c5c312295',
            u'dnt': u'1',
            u'Host': u'ezwzmmh526.execute-api.us-east-1.amazonaws.com',
            u'X-Forwarded-Proto': u'https',
            u'Referer': u'https://ezwzmmh526.execute-api.us-east-1.amazonaws.com/Prod/approve?execution-id=9487c326-23fc-46d6-a2c2-69b6342b5162&task-token=AAAAKgAAAAIAAAAAAAAAAbwck0ZXLox0l5UCsjE3iQN3iBJNAu9ZWh%2FElSrNKHdVP90ZxgrPZvFQZMnl%2BdcD4J9VdwieXvx2s6VBpQ1AsIrJLYM7y9D1bDRvrct34LA4YldibA7gw3dz5YmvScrCiLX8DLPT5BiKkpKtwN5pVXqlC0fZcSQ4Z2ZdSvAN%2Fawy6S678p5QyxsJlqe3pQpbIZfmQ4XjboqpLMIWSMDkYajtBuxMgtfyX879s5QHzCZ9d0B29WI3FV0PS07xMYrqn%2B2Nu%2F2l64JvKMMNBknJZiM2c92AQFZMFvOvMCHnxbtLqZjZpWTaW5Z3O0Cv5B91l6T7bZvk6Dp7QZ6fAdYlQw8S%2FYT0Vz6z%2FsMPDf3bxPfGJ9b4cjVHbLX0nK4BEvlAW%2FOEXJGGYG9X2V%2FgUoRMs%2FRwEenzvxi5raZPsHlCqOZzmuszC1H4duNQBaRjF2vzOY60wyOoP7%2FshrdfPvGKh9LMMUi%2Fir2y9W8hbCb6R1MZERE9yOIUlK%2Bc5NHZf64JnRvNG2tUF4efOjVIbZfLrayDEAgLqeOtlXSy7yOLxSjdmqcVKXmD2AdnLg2yi%2FHYyyUc3fQPZES6nPOMpuLz27E%3D',
            u'CloudFront-Is-Tablet-Viewer': u'false',
            u'X-Forwarded-Port': u'443',
            u'X-Amz-Cf-Id': u'ZVhtdhkgqjEmMBhWxew_9Xuq91gaPrxLIowzD0R0eBJgXzXj8Y6rfQ==',
            u'CloudFront-Is-Mobile-Viewer': u'false',
            u'content-type': u'application/json',
            u'CloudFront-Is-Desktop-Viewer': u'true'
        },
        u'stageVariables': None,
        u'path': u'/deny',
        u'isBase64Encoded': False
    }
    print("Lambda Handler:")
    print(lambda_handler(EVENT, {}))
