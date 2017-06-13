import string
import boto3
import json
import re
import os
from requests.utils import unquote

try:
    session = boto3.session.Session(profile_name='training', region_name='us-east-1')
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
        return "https://{domain}/{stage}/".format(  domain=event['headers']['Host'],
                                                    stage=event['requestContext']['stage'])
    else:
        return "https://{domain}/".format(domain=event['headers']['Host'])


def return_step_function_token_task(event, domain):

    sfn_client = session.client('stepfunctions')
    approved_or_denied = event["pathParameters"].get("approval", "deny")
    body = json.loads(event['body'])
    task_token = unquote(body['task_token'])


    response_string = ''

    print(approved_or_denied)
    print(body)

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
    # returns a website front end for approval
    dynamodb_client = session.client('dynamodb')
    entity_arn  = ''
    entity_name = ''

    try:
        execution_id = event['queryStringParameters']['execution-id']
        print(execution_id)
        response_item   = dynamodb_client.get_item( TableName="security_fairy_dynamodb_table",#os.environ['dynamodb_table'],
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
    event = {u'body': None, u'resource': u'/{approval}', u'requestContext': {u'resourceId': u'ktk3jq', u'apiId': u'ezwzmmh526', u'resourcePath': u'/{approval}', u'httpMethod': u'GET', u'requestId': u'f19b3050-5491-11e7-962e-117aa41f93fd', u'path': u'/Prod/approve', u'accountId': u'281782457076', u'identity': {u'apiKey': u'', u'userArn': None, u'cognitoAuthenticationType': None, u'accessKey': None, u'caller': None, u'userAgent': u'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36', u'user': None, u'cognitoIdentityPoolId': None, u'cognitoIdentityId': None, u'cognitoAuthenticationProvider': None, u'sourceIp': u'71.219.125.215', u'accountId': None}, u'stage': u'Prod'}, u'queryStringParameters': {u'execution-id': u'4b44f8ba-c3ef-438a-bb66-c3d2ee8ba625', u'task-token': u'AAAAKgAAAAIAAAAAAAAAAWz8LPM/DsVFhs0RQ66Vsv3lxqZvp+r94yjZnw89lRDw/GS/BHY6we+yz5cnYI3n2NjD9lL9VEYrw17FvH+XNcqZTyKNnMJce+U4joLGJkP2LdMAWmhJP1SqUGWwI3p/L9i2iiKAl/vCtPyafAEShC5XHSoK4+2CG5ga12jQBZwn26JPSdnaCwVLP3qnRSiaZooAEXD9UxmgVrMSSDDWgRF/uNJvz+Fu4s0DiC739h5V0yeODZtpt3OsCJ3jF/xUA2xhuAcDYk4sbOnS7I9I2qaGTv86DoAF5rigMAemDecw8tV5hgDRyF1o7yLT4np34R+zMjNEDiW9r7lIq/OhqaBMWhemKz+hIqWxikECIGB7aICnVlv120zOsN3e/cq54mFaC/2cXyhSsGO/Fa0wqUDkHeG3l1eJjxxXENOmip+wLRm7WNQB1JJ6MAxfg3iacO88dpbrrSS+6ZU9DW1nP09pQJdys8A+Bq/vVGlvIZRRJ7Ncz632R4MbPi5X60jvBFCxFHAOoFt31Ba9YRTh+jHEtnOgjWNf1CG1QDqwoJSHuwRY1hQVz5jvivsVDK07+ePtN2XmIwTbCE4DVTeMvBw='}, u'httpMethod': u'GET', u'pathParameters': {u'approval': u'approve'}, u'headers': {u'Via': u'2.0 67ced1de1dff09be998d5f2fbf3fa67b.cloudfront.net (CloudFront)', u'Accept-Language': u'en-US,en;q=0.8', u'CloudFront-Is-Desktop-Viewer': u'true', u'CloudFront-Is-SmartTV-Viewer': u'false', u'X-Forwarded-Port': u'443', u'CloudFront-Is-Mobile-Viewer': u'false', u'X-Forwarded-For': u'71.219.125.215, 205.251.214.65', u'CloudFront-Viewer-Country': u'US', u'Accept': u'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8', u'upgrade-insecure-requests': u'1', u'X-Amzn-Trace-Id': u'Root=1-59472e59-00acdffb20900a7344ea0542', u'dnt': u'1', u'Host': u'ezwzmmh526.execute-api.us-east-1.amazonaws.com', u'X-Forwarded-Proto': u'https', u'X-Amz-Cf-Id': u'wvvWpayfsHwfP8c_2QMCY4Zdq_cUt-kxj3kQZ_DPH_2lKkY-xMWL3Q==', u'CloudFront-Is-Tablet-Viewer': u'false', u'cache-control': u'max-age=0', u'User-Agent': u'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36', u'CloudFront-Forwarded-Proto': u'https', u'Accept-Encoding': u'gzip, deflate, sdch, br'}, u'stageVariables': None, u'path': u'/approve', u'isBase64Encoded': False}
    print(lambda_handler(event, {}))
