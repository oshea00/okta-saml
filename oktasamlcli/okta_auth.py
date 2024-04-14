""" Handles auth to Okta and returns SAML assertion """
# pylint: disable=C0325,R0912,C1801
# Incorporates flow auth code taken from https://github.com/Nike-Inc/gimme-aws-creds
import sys
import re
from codecs import decode
import requests
from bs4 import BeautifulSoup as bs

class OktaAuth():
    """ Handles auth to Okta and returns SAML assertion """
    def __init__(self, okta_profile, verbose, logger, totp_token,
        okta_auth_config, username, password, verify_ssl=True):

        self.okta_profile = okta_profile
        self.totp_token = totp_token
        self.logger = logger
        self.verbose = verbose
        self.verify_ssl = verify_ssl
        self.factor = okta_auth_config.factor_for(okta_profile)
        self.app_link = okta_auth_config.app_link_for(okta_profile)
        self.okta_auth_config = okta_auth_config
        self.session = None
        self.session_token = ""
        self.session_id = ""
        self.https_base_url = "https://%s" % okta_auth_config.base_url_for(okta_profile)
        self.auth_url = "%s/api/v1/authn" % self.https_base_url

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
