""" Handles auth to Okta and returns SAML assertion """
# Copyright 2024 Michael OShea
# pylint: disable=C0325,R0912,C1801
import sys
from codecs import decode
import requests
from bs4 import BeautifulSoup as bs
from requests.auth import HTTPBasicAuth

class OktaAuth():
    """ Handles auth to Okta and returns SAML assertion """
    def __init__(self, okta_profile, verbose, logger,
        okta_auth_config, username, password, verify_ssl=True):

        self.okta_profile = okta_profile
        self.logger = logger
        self.verbose = verbose
        self.verify_ssl = verify_ssl
        self.app_link = okta_auth_config.app_link_for(okta_profile)
        self.okta_auth_config = okta_auth_config
        self.session = None
        self.session_token = ""
        self.session_id = ""
        self.https_base_url = "https://%s" % okta_auth_config.base_url_for(okta_profile)
        self.auth_url = "%s/api/v1/authn" % self.https_base_url
        self.scope = okta_auth_config.scope_for(okta_profile)
        self.issuer_url = okta_auth_config.issuer_url_for(okta_profile)
        self.authorization_code = ""
        self.access_token = ""

        if username:
            self.username = username
        else:
            self.username = okta_auth_config.username_for(okta_profile)

        if password:
            self.password = password
        else:
            self.password = okta_auth_config.password_for(okta_profile)

    def primary_auth(self):
        """ Performs primary auth against Okta """

        auth_data = {
            "username": self.username,
            "password": self.password
        }
        self.session = requests.Session()
        resp = self.session.post(self.auth_url, json=auth_data)
        resp_json = resp.json()
        self.cookies = resp.cookies
        if 'status' in resp_json:
            if resp_json['status'] == 'SUCCESS':
                session_token = resp_json['sessionToken']
            elif resp_json['status'] == 'LOCKED_OUT':
                self.logger.error("""Account is locked. Cannot continue.
Please contact you administrator in order to unlock the account!""")
                sys.exit(1)
        elif resp.status_code != 200:
            self.logger.error(resp_json['errorSummary'])
            sys.exit(1)
        else:
            self.logger.error(resp_json)
            sys.exit(1)


        return session_token


    def get_session(self, session_token):
        """ Gets a session cookie from a session token """
        data = {"sessionToken": session_token}
        resp = self.session.post(
            self.https_base_url + '/api/v1/sessions', json=data).json()
        return resp['id']


    def get_simple_assertion(self, html):
        soup = bs(html.text, "html.parser")
        for input_tag in soup.find_all('input'):
            if input_tag.get('name') == 'SAMLResponse':
                return input_tag.get('value')

        return None

    def get_saml_assertion(self, html):
        """ Returns the SAML assertion from HTML """
        assertion = self.get_simple_assertion(html)

        if not assertion:
            self.logger.error("SAML assertion not valid: " + assertion)
            sys.exit(-1)
        return assertion


    def get_assertion(self):
        """ Main method to get SAML assertion from Okta """
        self.session_token = self.primary_auth()
        self.session_id = self.get_session(self.session_token)
        app_name = None
        self.session.cookies['sid'] = self.session_id
        resp = self.session.get(self.app_link)
        assertion = self.get_saml_assertion(resp)
        return app_name, assertion
    
    def get_auth_code(self, client_id):
        """ Main method to get authorization code from Okta """
        payload = {
            'client_id' : client_id,
            'response_type' : 'code',
            'response_mode' : 'form_post',
            'scope' : self.scope,
            'redirect_uri' : 'http://localhost:8080/authorization-code/callback', #Dummy URI
            'state' : 'none'
        }
        resp = self.session.get(f'{self.issuer_url}/v1/authorize', params=payload)
        soup = bs(resp.content, 'html.parser')
        try:
            self.authorization_code = soup.find_all(attrs={"name": "code"})[0]['value']
        except:
            self.logger.error('Unable to retrieve authorization code. Verify Okta config.')
            sys.exit(-1)
    
    def get_jwt_token(self, client_id, client_secret):

        headers =  {
            'Accept' : 'application/json',
            'Content-Type' : 'application/x-www-form-urlencoded'
            }

        payload = {
            'grant_type' : 'authorization_code',
            'redirect_uri' : 'http://localhost:8080/authorization-code/callback', #Dummy URI
            'code' : self.authorization_code,
            'scope' : self.scope
        }

        response = requests.post(f'{self.issuer_url}/v1/token', auth=HTTPBasicAuth(client_id, client_secret), data=payload, headers=headers)

        jwt_decoded = None

        if response.status_code == 200:
            jwt_json = response.json()
            jwt_decoded = jwt_json['access_token']

        self.access_token = jwt_decoded
