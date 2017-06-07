import boto3

import boto3
import json
import re
import os

try:
    session = boto3.session.Session(profile_name='training')
except Exception as e:
    session = boto3.session.Session()


def lambda_handler(event, context):

    print(event)

    method = event['httpMethod']
    domain = get_domain(event)

    if method == 'GET' and event['queryStringParameters'] is not None:
        return retrieve_policy(event, domain)

    if method == 'POST':
        return return_token_task(event, domain)

    # Default API Response returns an error
    return api_return_payload = {
      'statusCode': 500,
      'headers':{
          'Content-Type':'application/json'
      },
      'body':'Interal Server Error'
    }



def get_domain(event):

    # Supports test invocations from API Gateway
    if event['headers'] is None:
        return "https://testinvocation/redirect"

    # Extracts the domain from event object based on for both api gateway URLs
    # or custom domains
    if 'amazonaws.com' in event['headers']['Host']:
        return "https://{domain}/{stage}/redirect".format(domain=event['headers']['Host'],
                                                          stage=event['requestContext']['stage'])
    else:
        return "https://{domain}/redirect".format(domain=event['headers']['Host'])

def return_token_task(event, domain):
    pass


def api_website(event, domain):
    # returns a website front end for the redirect tool
    body = """<html>
            <body bgcolor=\"#E6E6FA\">
            <head>
            <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
            <script>
            $(document).ready(function(){
                $("button").click(function(){
                  var destinationUrl = document.getElementById("destinationUrl").value;
                  var dict = {};
                  dict["destination_url"] = destinationUrl;
                  if (document.getElementById("customToken").value != "") {
                      dict["custom_token"] = document.getElementById("customToken").value;
                  }
                  $.ajax({
                    type: 'POST',
                    headers: {
                        'Content-Type':'application/json',
                        'Accept':'text/html'
                    },
                    url:'"""

    body += domain
    body +=         """',
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
            <body>"""
    body += event['resource'][1:]
    body += """<form class="form" action="" method="post">
                    <textarea rows="1" cols="50" name="text" id="destinationUrl" placeholder="Enter URL (http://www.example.com)"></textarea>
              </form>
              <form class="form" action="" method="post">
                    <textarea rows="1" cols="50" name="text" id="customToken" placeholder="Use Custom Token (domain.com/redirect/custom_token)"></textarea>
              </form>
            <button>Shorten URL</button>
            <div id='id'></div>
            </body>
            </html>"""

    return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": 'text/html',
                    "Access-Control-Allow-Origin": "*"
                },
                "body": body
    }


if __name__ == '__main__':
    event = {
  "body": "{\"test\":\"body\"}",
  "resource": "/{proxy+}",
  "requestContext": {
    "resourceId": "123456",
    "apiId": "1234567890",
    "resourcePath": "/{proxy+}",
    "httpMethod": "POST",
    "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
    "accountId": "123456789012",
    "identity": {
      "apiKey": null,
      "userArn": null,
      "cognitoAuthenticationType": null,
      "caller": null,
      "userAgent": "Custom User Agent String",
      "user": null,
      "cognitoIdentityPoolId": null,
      "cognitoIdentityId": null,
      "cognitoAuthenticationProvider": null,
      "sourceIp": "127.0.0.1",
      "accountId": null
    },
    "stage": "prod"
  },
  "queryStringParameters": {
    "foo": "bar"
  },
  "headers": {
    "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
    "Accept-Language": "en-US,en;q=0.8",
    "CloudFront-Is-Desktop-Viewer": "true",
    "CloudFront-Is-SmartTV-Viewer": "false",
    "CloudFront-Is-Mobile-Viewer": "false",
    "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
    "CloudFront-Viewer-Country": "US",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Upgrade-Insecure-Requests": "1",
    "X-Forwarded-Port": "443",
    "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
    "X-Forwarded-Proto": "https",
    "X-Amz-Cf-Id": "cDehVQoZnx43VYQb9j2-nvCh-9z396Uhbp027Y2JvkCPNLmGJHqlaA==",
    "CloudFront-Is-Tablet-Viewer": "false",
    "Cache-Control": "max-age=0",
    "User-Agent": "Custom User Agent String",
    "CloudFront-Forwarded-Proto": "https",
    "Accept-Encoding": "gzip, deflate, sdch"
  },
  "pathParameters": {
    "proxy": "path/to/resource"
  },
  "httpMethod": "POST",
  "stageVariables": {
    "baz": "qux"
  },
  "path": "/path/to/resource"
}


    lambda_handler(event, {})
