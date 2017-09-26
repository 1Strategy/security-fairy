import string
import logging

def api_response(statusCode=500, headers={'Content-Type':'text/html'}, body='Internal Service Error'):
    if statusCode < 100 or statusCode > 599:
        raise ValueError('Invalid HTTP statusCode')

    return_value =  {
                'statusCode': statusCode,
                'headers'   : headers,
                'body'      : body
            }

    logging.debug(return_value)
    return return_value


def get_domain_from_proxy_api_gateway(event):

    if event['headers'] is None:
        return "https://testinvocation/approve"

    if 'amazonaws.com' in event['headers']['Host']:
        return "https://{domain}/{stage}/".format(  domain=event['headers']['Host'],
                                                    stage=event['requestContext']['stage'])
    else:
        return "https://{domain}/".format(domain=event['headers']['Host'])


def api_website(website_body='', safe_substitute_dict={'domain':'http://example.domain'}):
    logging.debug(website_body)
    logging.debug(safe_substitute_dict)

    body = website_body if website_body else \
            """
            <html>
            <body>
            <title>Webpage serverd from API Gateway and Lambda</title>
            <h1>This is an example of an HTTP Get Responses for a Lambda/API Gateway served website</h1>
            The domain is: $domain
            </body>
            </html>
            """

    logging.debug(body)

    if website_body and safe_substitute_dict:
        for variable in safe_substitute_dict:
            if '${variable}'.format(variable=variable) not in body:
                logging.debug('${variable}'.format(variable=variable))
                raise ValueError('A variable to be replaced in the body must be represented by a $variable')

    compiled_body   = string.Template(body).safe_substitute(safe_substitute_dict)
    logging.debug(compiled_body)
    return api_response(statusCode=200, body=compiled_body)
