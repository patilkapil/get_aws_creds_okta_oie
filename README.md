## get_creds is a CLI utility for Okta OIE + AWS FED app to acquire temporary AWS credentials via AWS STS.

```diff
- Code doesn't handle expiry of AWS credentials at the moment 
```
 
# Assumption
1. You have an AWS FED App already set
2. You have AWS OAuth app tied to AWS FED app
3. Tenant is enabled for the new AWS FED app

# Setup Instructions 
 
Download the latest get_creds package direct from GitHub:

https://github.com/patilkapil/get_aws_creds_okta_oie.git
 

# Install the get_creds package  

Run the following command, where GIT code has been downloaded

```python setup.py install  ```
Running above command will create a python package. More information here:  https://gehrcke.de/2014/02/distributing-a-python-command-line-application/

Running this file will give you the output:
![image](https://user-images.githubusercontent.com/2838125/168669769-ce865c26-096a-429c-b5da-a549b458893e.png)



get_creds package will be installed on a library path. Makre sure to include this library path on your environment variables. 

# Configuration

Currently all the configurations are hard coded (To be changed) in the file ```get_credy.py ```
```
env_conf_map={
'OIDC_CLIENT_ID':'XXXXX',
'DEFAULT_OKTA_AUTHZ_SERVER':'https://<domain>/oauth2/v1/token',
'GRANT_TYPE':'urn:ietf:params:oauth:grant-type:device_code',
'AUDIENCE_SSO':'urn:okta:apps:YYY',
'SAML_ASSERTION_URL':'https://<domain>/login/token/sso?token=',
'DEVICE_AUTHORIZATION_URL':'https://<domain>/oauth2/v1/device/authorize'
}
```

 Replace your Okta tenant's respective values. 
 
 # Execution
 
 Once python package has been installed, you can run the get_creds command
<img width="798" alt="image" src="https://user-images.githubusercontent.com/2838125/168671355-48b2e1a2-1d5a-4764-937f-492b9c01aa9a.png">


You will notice updated profile section in local .aws\config section


<img width="476" alt="image" src="https://user-images.githubusercontent.com/2838125/168672628-80983c87-3a37-4e88-861e-c2ccdec3a205.png">


Switch to a new profile and start using aws cli commands 

<img width="678" alt="image" src="https://user-images.githubusercontent.com/2838125/168673150-65e1171e-5bdf-4e81-9921-9ad527bcc33a.png">

## Sequence Diagram 

![image](https://user-images.githubusercontent.com/2838125/171256580-09dfa436-0405-4cec-944e-e68cac44d4b6.png)




### THIS IS A PROTOTYPE AND HAS NOT BEEN THROUTROUGHLY TESTED FOR EVERY USE CASE.
