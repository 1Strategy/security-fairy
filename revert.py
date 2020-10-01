import boto3
import json
import logging
import os
import re
from aws_entity     import AWSEntity
from setup_logger   import create_logger
from aws_api_tools  import api_response
from aws_api_tools  import api_website
from aws_api_tools  import get_domain_from_proxy_api_gateway
from botocore.exceptions        import ProfileNotFound
from boto3.dynamodb.conditions  import Key

logger = create_logger(name = "revert.py", logging_level=logging.INFO)

try:
    SESSION = boto3.session.Session(profile_name='sandbox',
                                    region_name='us-east-1')
except ProfileNotFound as pnf:
    SESSION = boto3.session.Session()


def lambda_handler(event, context):

    method = event['httpMethod']

    if method == 'GET':
        logger.info('Request was an HTTP GET Request')
        return get_response(event)

    if method == 'POST':
        logger.info('Request was an HTTP POST Request')
        posted_arn = json.loads(event['body'])['entity_arn']
        logger.info('Body: {}'.format(posted_arn))
        aws_entity = AWSEntity(posted_arn)
        return post_response(aws_entity)

    return api_response()


def get_response(event):
    entities = get_all_iam_audited_entities()
    # logger.info(type(entities))
    existing_entities = nosql_to_list_of_dicts(entities)

    for entity in existing_entities[0]:
        logging.debug(entity)
        logging.debug(type(entity))

    domain = get_domain_from_proxy_api_gateway(event)

    body = """
            <html>
            <body bgcolor="#E6E6FA">
            <head>
            <!-- Latest compiled and minified CSS -->
            <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
            <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
            <style>
            .code {
                max-height: 500px;
                max-width: 900px;
                overflow: scroll;
                text-align: left;
                margin-bottom: 20px;
            }
            th, td {
              text-align: left;
              padding: 15px;
              height: 50px;
              vertical-align: top;
              border-bottom: 1px solid #ddd;
            }
            td {
               font-size:x-small;
            }
            </style>
            <script>
            var dict = {};
            function submitRequest(revert){
                dict["entity_arn"] = document.getElementById("entity_arn").value;
                $.ajax({
                  type: 'POST',
                  headers: {
                      'Content-Type':'application/json',
                      'Access-Control-Allow-Origin': '*',
                      'Accept':'text/html'
                  },
                  url:'$domain' + 'revert',
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
                var name= document.getElementById("entity_arn").value.split("/")[1];
                var url = "https://console.aws.amazon.com/iam/home?region=us-east-1#/roles/"+name;
                document.location.href = url;
            };

            $(document).ready(function(){

                //document.getElementById("output").innerHTML = JSON.stringify({}, null, "\t");
                $("#revert").click(function(){
                  console.log("Approve button clicked");
                  submitRequest("revert");
                  setTimeout(redirect,4000);
                });
                $("#cancel").click(function(){
                  console.log("Cancel button clicked");
                  setTimeout(redirect,500);
                });
            });

            </script>
            </head>
            <body>
            <center>
            <title>IAM Security Fairy</title>
            <h1><span class="glyphicon glyphicon-fire text-danger" ></span> IAM Security Fairy</h1>

            <div class="code"><pre>
            <table class="code">
              <tr>
                <th>Execution Id</th>
                <th>Role ARN</th>
                <th>Original Managed Policies</th>
              </tr>
              $security_fairy_entities_list
            </table>
            </pre></div>
            <div class="code"><pre id='output' style="visibility:hidden;"></pre></div>
            <div class="code">Enter the arn of the role you would like to revert:<br>
            <form style= "display: inline-block;" action="" method="post">
                <textarea rows="1" cols="40" name="text" id="entity_arn" placeholder="arn:aws:iam::0123456789:role/roleName"></textarea>
            </form>
            <button style= "display: inline-block;margin-bottom: 20px;" class="btn btn-primary" id='revert'>Revert</button>
            <button style= "display: inline-block;margin-bottom: 20px;" class="btn btn-danger" id='cancel'>Cancel</button>
            </div>
            </center>
            </body>
            </html>"""

    logger.info(existing_entities[0])
    security_fairy_entities_list = ''
    for entity in existing_entities:
        table_row = """<tr>
                          <td>{execution_id}</td>
                          <td>{entity_arn}</td>
                          <td>""".format(execution_id=entity['execution_id'],
                                         entity_arn=entity['entity_arn'])

        for policy in entity['existing_policies']:
            table_row+= "{policy}<br>".format(policy=policy.split(':')[5])

        table_row+="</td></tr>"
        security_fairy_entities_list += table_row

    safe_substitute_dict = dict(domain = domain, security_fairy_entities_list=security_fairy_entities_list)
    return api_website(website_body=body, safe_substitute_dict=safe_substitute_dict)



def get_all_iam_audited_entities():

    dynamodb_client = SESSION.client('dynamodb')
    response_item   = dynamodb_client.scan( TableName='security_fairy_dynamodb_table',
                                            AttributesToGet=[
                                                'execution_id',
                                                'entity_arn',
                                                'existing_policies'
                                            ])['Items']
    logger.info(response_item)
    logger.info(type(response_item))
    return response_item


def post_response(aws_entity):
    try:
        revert_role_managed_policies(aws_entity)
    except Exception as e:
        # Generic "catch-all exception"
        logger.error(e)
        return api_response(body='Error - Role wasn\'t reverted properly.')

    return api_response(statusCode=200, headers={"Access-Control-Allow-Origin":"*", "Content-Type":"text/html"}, body='Success: The IAM Role has had it\'s pre-security fairy permissions established')


def revert_role_managed_policies(aws_entity):
    """
    Reverts role to pre-security fairy permissions
    """
    if not aws_entity.is_role():
        raise ValueError("The submitted ARN must be for a role.")

    associate_preexisting_policies(aws_entity)
    disassociate_security_fairy_policy(aws_entity)
    # delete_security_fairy_dynamodb_entry(aws_entity)

def get_preexisting_policies(entity_arn):

    dynamodb_client = SESSION.client('dynamodb')

    # reach out to security_fairy_dynamodb_table and get 'existing_policies' field
    response_item = dynamodb_client.scan(
                        TableName='security_fairy_dynamodb_table',
                        # IndexName='entity_arn',
                        # AttributesToGet=
                        # [
                        #     'execution_id',
                        #     'entity_arn',
                        #     'existing_policies'
                        # ],
                        ScanFilter={
                            'entity_arn': {
                                'AttributeValueList': [
                                    {
                                        'S': entity_arn
                                    }
                                ],
                                'ComparisonOperator': 'EQ'
                            }
                        }
                        )['Items'][0]

    logger.info(response_item)
    existing_policies = response_item['existing_policies']['SS']
    logger.info(existing_policies)

    return existing_policies


def associate_preexisting_policies(aws_entity):

    iam_client = SESSION.client('iam')

    entity_arn          = aws_entity.get_full_arn()
    existing_policies   = get_preexisting_policies(entity_arn)
    role_name           = aws_entity.get_entity_name()
    # for each item in 'existing_policies' attach policy to 'role_arn'
    for policy in existing_policies:
        logger.info(policy)
        attachment_response = iam_client.attach_role_policy(RoleName=role_name,
                                                            PolicyArn=policy)


def disassociate_security_fairy_policy(aws_entity):
    iam_client      = SESSION.client('iam')

    account_number  = aws_entity.get_account_number()
    entity_name     = aws_entity.get_entity_name()

    policy_arn      =  'arn:aws:iam::{account_number}:policy/security-fairy/{entity_name}-security-fairy-revised-policy'\
                            .format(account_number=account_number,
                                    entity_name=entity_name)\
                                        .replace('_','-')
    logger.info(policy_arn)

    try:
        detach_policy(entity_name, policy_arn)
        delete_policy(policy_arn)
    except iam_client.exceptions.NoSuchEntityException as error:
         logging.info("Error deleting or detaching policy from role: {}, the entity doesn't exist.".format(error))

def detach_policy(entity_name, policy_arn):
    iam_client      = SESSION.client('iam')
    iam_client.detach_role_policy(RoleName=entity_name, PolicyArn=policy_arn)
    logging.info("Detaching {} from {}".format(entity_name, policy_arn))



def delete_policy(policy_arn):

    iam_client      = SESSION.client('iam')
    policy_versions = iam_client.list_policy_versions( PolicyArn=policy_arn)['Versions']

    for version in policy_versions:
        if not version['IsDefaultVersion']:
            iam_client.delete_policy_version(   PolicyArn=policy_arn,
                                                VersionId=version['VersionId'])
    iam_client.delete_policy(PolicyArn=policy_arn)

def nosql_to_list_of_dicts(dynamodb_response_item):
    refactored_dicts = []
    for item in dynamodb_response_item:
        refactored_item = {}
        for key in item:
            for nested_key in item[key]:
                refactored_item[key] = item[key][nested_key]
        refactored_dicts.append(refactored_item)
    return(refactored_dicts)



if __name__ == '__main__':
    # entity_arn = 'arn:aws:iam::281782457076:role/1s_tear_down_role'
    # disassociate_security_fairy_policy(entity_arn)
    # delete_policy('arn:aws:iam::281782457076:policy/security-fairy/1s-tear-down-role-security-fairy-revised-policy')
    # associate_preexisting_policies("arn:aws:iam::281782457076:role/1s_tear_down_role")
    # get_all_iam_audited_entities()
    # print(nosql_to_list_of_dicts(get_all_iam_audited_entities()))
    event = {
                "resource":"/revert",
                "path":"/revert",
                "httpMethod":"GET",
                "headers":None,
                "queryStringParameters":None,
                "pathParameters":None,
                "stageVariables":None,
                "cognitoAuthenticationType":None,
                u'headers': {
                    u'origin': u'https://twzwjoriak.execute-api.us-east-1.amazonaws.com',
                    u'Accept': u'text/html',
                    u'Host': u'twzwjoriak.execute-api.us-east-1.amazonaws.com'
                },
                u'requestContext': {
                    u'resourceId': u'ktk3jq',
                    u'apiId': u'ezwzmmh526',
                    u'resourcePath': u'/{approval}',
                    u'httpMethod': u'GET',
                    u'requestId': u'2938ad50-50a7-11e7-bff1-93579d44e732',
                    u'path': u'/Prod/approve',
                    u'accountId': u'281782457076',
                    u'stage': u'Prod'
                }
            }
    # lambda_handler(event, {})


    # dynamodb_response_item = [{u'entity_arn': {u'S': u'arn:aws:iam::281782457076:role/1s_tear_down_role'}, u'existing_policies': {u'SS': [u'arn:aws:iam::281782457076:policy/1S-NetworkAdmin-Policy', u'arn:aws:iam::281782457076:policy/AccessNavigationNotebookObjects', u'arn:aws:iam::281782457076:policy/AllowAuroraToGdeltBucket', u'arn:aws:iam::281782457076:policy/AllowUserChangePassword', u'arn:aws:iam::aws:policy/AdministratorAccess']}, u'execution_id': {u'S': u'4c0201ab-76e3-4c42-80ed-fdd99f5968cf'}}]
    # print(type(dynamodb_response_item))
    logger.info(get_response(event)['body'].strip('\n'))
