import configparser
import json
import os
import re
import time
import boto3
from html import unescape
import xml.etree.ElementTree as ET
import requests
import base64
import platform
from dotenv import load_dotenv
from pathlib import Path
import pkg_resources

#TODO : Move to a config file#
'''
Defining the list of configuration parameters:
OIDC_CLIENT_ID - OAuth app you have set in Okta, same App ID you used in your AWS-FED OIN app
DEFAULT_OKTA_AUTHZ_SERVER-'https://<Okta Domain>/oauth2/v1/token , address of your default Okta Authz server
GRANT_TYPE - 'Grant type to be used for the device flow
AUDIENCE_SSO - Audience value to be used to Okta's API  /login/token/sso?token={{access_token_saml}}
SAML_ASSERTION_URL - SAML assertions URL to receive the SAML response 
DEVICE_AUTHORIZATION_URL - URL to authorize user's device end point'
'''
env_conf_map={
'OIDC_CLIENT_ID':'XXXXX',
'DEFAULT_OKTA_AUTHZ_SERVER':'https://<Domain>/oauth2/v1/token',
'GRANT_TYPE':'urn:ietf:params:oauth:grant-type:device_code',
'AUDIENCE_SSO':'urn:okta:apps:YYYYYY',
'SAML_ASSERTION_URL':'https://<Domain>/login/token/sso?token=',
'DEVICE_AUTHORIZATION_URL':'https://<Domain>/oauth2/v1/device/authorize'
}


def check_device_validation(device_code,user_code,verification_uri):
  """

  :param device_code: device code returned by user's action. Device code will be used to validate if user has been activated or not
  :param user_code: User code, is the code used by a user to activate
  :param verification_uri: Verification URI to be used by a user for activation
  :return: After user is validated, control will be passed on to receive access and security token
  """
  payload='client_id='+env_conf_map['OIDC_CLIENT_ID']+'&device_code='+device_code+'&grant_type='+env_conf_map['GRANT_TYPE']
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  }

  print('Activate your device for the AWS CLI access using the following Code+URL.')
  print("Activation URL-  "+verification_uri)
  print('User Code-   '+user_code)
  json_str=""
  #Inside the While loop till the user is activated.Introducing a delay of 10 sec.
  #after every 10 sec, code will check if a user has been activated.
  while "token_type" not in json_str:
    response = requests.request("POST", env_conf_map['DEFAULT_OKTA_AUTHZ_SERVER'], headers=headers, data=payload)
    json_str = json.loads(response.text)
    time.sleep(10)
  else:
    #When activation has been completed make a call to the Okta's SSO Token API end point
    #Retrieve Access,ID Token values and Scope
    get_sso_token(json_str['access_token'],json_str['id_token'],json_str['scope'])


def update_aws_config(credentials,profile):
  '''
  Update AWS config file will update the local config file with values from AWS STS API end point
  aws_access_key_id
  aws_secret_access_key_id
  aws_session_token
  :param credentials: Credentials data for the AWS Assumed role
  :param profile: Name of the profile
  '''
  #Config parser to read local aws config file based on your system
  config = configparser.ConfigParser()
  if platform.system()!="Windows":
    config.read(os.path.expanduser("~/.aws/config"))
  else:
    config.read(os.path.expanduser("~/.aws/config"))
    #TODO Test it on a windows machine ***#
  if config.has_section(profile):
    #Update an exiasting profile properties
    config[profile]["aws_access_key_id"] = credentials["AccessKeyId"]
    config[profile]["aws_secret_access_key_id"] = credentials["SecretAccessKey"]
    config[profile]["aws_session_token"] = credentials["SessionToken"]
  else:
    #Create a new profile name and update with credentials attribute
    config.add_section(profile)
    config[profile]["aws_access_key_id"] = credentials["AccessKeyId"]
    config[profile]["aws_secret_access_key_id"] = credentials["SecretAccessKey"]
    config[profile]["aws_session_token"] = credentials["SessionToken"]

  #TODO : Check with Windows *****#
  #Update existing config files with new config objects
  if platform.system()!="Windows":
    with open(os.path.expanduser("~/.aws/config"), 'w') as configfile:
      config.write(configfile)
  else:
    with open(os.path.expanduser("~/.aws/config"), 'w') as configfile:
      config.write(configfile)

  print("Profile Name- "+profile+" has been updated on your local /.aws/config,Now you can start using aws-cli commands")

def get_sts_token(awsrole,assertion,profile):
  '''
  STS API token end point,will be invoked by STS assume Role and it will return back the credentials.
  :param awsrole: AWS role to be used by a user
  :param assertion: SAML assertions
  :param profile: Name of the Profile to be used by AWS CLI
  This function will call update aws config and will update the local .aws/config file
  '''
  #Get boto3 client
  sts = boto3.client('sts')
  #Split AWS Role and IAM Value
  awsrole = awsrole.split(",")
  #Call STS Assume role to retrieve AWS credentials
  response = sts.assume_role_with_saml(RoleArn=awsrole[1],
                                       PrincipalArn=awsrole[0],
                                       SAMLAssertion=assertion)
  credentials = response['Credentials']
  #Call to update AWS local  config
  update_aws_config(credentials,profile)



def get_saml_assertion(access_token):
  '''
   This methos will call the SAML assertion endpoint and will retrieve the SAML response.
   SAML response is in the form of HTML.
   Code parses HTML response and retrieves all the IDP+ AWS IAM Role combination.
   Function will list all the AWS Roles a user can assume and will take the input : Which role user would like to assume
   Post user selection, code will invoke STS API endpoint to retrieve AWS credentials along with SAML assertions
  :param access_token: Access token returned by the Authz default server endpoint

  '''
  #Create a URL for SAML assertions
  url = env_conf_map['SAML_ASSERTION_URL']+ access_token
  #Make a GET request
  r = requests.get(url)
  #Logic to retrive SAML assertions
  match = re.search(r'<input name="SAMLResponse".*value="([^"]*)"',
                    r.text)
  assertion = unescape(match.group(1))
  root = ET.fromstring(base64.b64decode(assertion))
  awsroles = []
  #Iterate through SAML response to retrieve AWS Roles
  for saml2attribute in root.iter('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
    if (saml2attribute.get('Name') == 'https://aws.amazon.com/SAML/Attributes/Role'):
      for saml2attributevalue in saml2attribute.iter('{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'):
        awsroles.append(saml2attributevalue.text)
  print('Set of available roles -')
  counter = 1
  aws_detail=[]
  #Print AWS Roles
  for awsrole in awsroles:
    aws_detail=awsrole.split(",")
    print("Choice-",counter)
    counter=counter+1
    print("IDP -" + aws_detail[0])
    print("AWS Role -" + aws_detail[1])
  #Get AWS Role value
  num = input("Enter Your choice number :")
  profile = input("Enter the Profile name :")
  print("Getting STS credentials by assuming the role")
  get_sts_token(awsroles[int(num)-1],assertion,profile)




def get_sso_token(access_token,id_token,scope):
  '''
  After Device validation, invoke default Authz Server token endpoint
  :param access_token: Access Token
  :param id_token: Id token
  :param scope: Scope
  :return: Response from the Authz server would will be parsed and access token will be used to get SAML assertions
  '''

  #Create a POST payload
  payload = 'client_id='+env_conf_map['OIDC_CLIENT_ID']+\
            '&actor_token='+access_token+\
            '&actor_token_type=urn%3Aietf%3Aparams%3Aoauth%3Atoken-type%3Aaccess_token' \
            '&subject_token='+id_token+\
            '&subject_token_type=urn%3Aietf%3Aparams%3Aoauth%3Atoken-type%3Aid_token' \
            '&grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Atoken-exchange' \
            '&requested_token_type=urn%3Aokta%3Aoauth%3Atoken-type%3Aweb_sso_token' \
            '&audience='+env_conf_map['AUDIENCE_SSO']
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  }

  response = requests.request("POST", env_conf_map['DEFAULT_OKTA_AUTHZ_SERVER'], headers=headers, data=payload)
  json_str = json.loads(response.text)
  #Parse the response and grab the access token & call the SAML assertion method
  get_saml_assertion(json_str['access_token'])

#TODO : function to read config file#
'''def read_environment():
  resource_package = __name__
  resource_path = 'config.env'  # Do not use os.path.join()
  template = pkg_resources.resource_string(resource_package, resource_path)
  oidc_client_id=1
  # = Path()
  #basedir = str(basepath.cwd())
  # Load the environment variables
  #envars = basepath.cwd() / 'config.env'
  load_dotenv(".env")'''




def main():
  payload='client_id='+env_conf_map['OIDC_CLIENT_ID']+'&scope=openid%20okta.apps.sso'
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  }
  response = requests.request("POST", env_conf_map['DEVICE_AUTHORIZATION_URL'], headers=headers, data=payload)
  json_str=json.loads(response.text)
  print(json_str)
  device_code=json_str["device_code"]
  check_device_validation(json_str["device_code"],json_str["user_code"],json_str["verification_uri"])




