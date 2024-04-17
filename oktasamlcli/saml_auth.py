""" Saml authentication """
# pylint: disable=C0325
# Copyright 2024 Michael OShea
import os
import base64
import xml.etree.ElementTree as ET
from collections import namedtuple
from configparser import RawConfigParser
from enum import Enum
from subprocess import call
import base64
import json
import time

class SamlAuth():
    """ Methods to support Saml api authentication using jwt """

    def __init__(self, profile, okta_profile, verbose, logger):
        home_dir = os.path.expanduser('~')
        self.creds_dir = home_dir + "/.saml"
        self.creds_file = self.creds_dir + "/credentials"
        self.profile = profile
        self.verbose = verbose
        self.logger = logger
        self.role = ""
        
        okta_config = home_dir + '/.okta-saml'
        parser = RawConfigParser()
        parser.read(okta_config)

        if parser.has_option(okta_profile, 'profile') and not profile:
            self.profile = parser.get(okta_profile, 'profile')
            self.logger.debug("Setting saml profile to %s" % self.profile)

    def set_default_profile(self, parser: RawConfigParser):
        if not parser.has_section('default'):
            parser.add_section('default')
        for key, value in parser.items(self.profile):
            parser.set('default', key, value)
        self.logger.info("Setting default profile.")
        with open(self.creds_file, 'w+') as configfile:
            parser.write(configfile)

    def check_jwt_expired(self,jwt_token):
        jwt_json = base64.b64decode(jwt_token.split('.')[1] + '==')
        exp = json.loads(jwt_json)['exp']
        return exp < time.time()

    def check_jwt_token(self):
        """ Verifies that jwt is valid """
        # Don't check for creds if profile is blank
        if not self.profile:
            return False

        parser = RawConfigParser()
        parser.read(self.creds_file)

        if not os.path.exists(self.creds_dir):
            self.logger.info("Saml credentials path does not exist. Not checking.")
            return False

        elif not os.path.isfile(self.creds_file):
            self.logger.info("Saml credentials file does not exist. Not checking.")
            return False

        elif not parser.has_section(self.profile):
            self.logger.info("No existing credentials found. Requesting new credentials.")
            return False

        # get jwt value from self.creds_file
        if parser.has_option(self.profile, 'jwt_session_token'):
            jwt_token = parser.get(self.profile, 'jwt_session_token')

            # parse token and check if it's expired
            # if expired, return False
            if self.check_jwt_expired(jwt_token):
                return False
        else:
            return False

        self.logger.info("Saml credentials are valid. Nothing to do.")
        SamlAuth.set_default_profile(self, parser)

        return True

    def write_jwt_token(self, session_token):
        """ Writes JWT auth information to credentials file """
        if not os.path.exists(self.creds_dir):
            os.makedirs(self.creds_dir)
        config = RawConfigParser()

        if os.path.isfile(self.creds_file):
            config.read(self.creds_file)

        if not config.has_section(self.profile):
            config.add_section(self.profile)

        config.set(self.profile, 'jwt_session_token', session_token)

        with open(self.creds_file, 'w+') as configfile:
            config.write(configfile)
        self.logger.info("Temporary credentials written to profile: %s" % self.profile)
        
        if self.profile != 'default':
            SamlAuth.set_default_profile(self, config)

    def extract_clientid_from(self, assertion):
        attribute = 'ClientID'
        attribute_value_urn = '{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'
        root = ET.fromstring(base64.b64decode(assertion))
        for saml2attribute in root.iter('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
            if saml2attribute.get('Name') == attribute:
                for saml2attributevalue in saml2attribute.iter(attribute_value_urn):
                    return saml2attributevalue.text
        return None

    def extract_clientsecret_from(self, assertion):
        attribute = 'ClientSecret'
        attribute_value_urn = '{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue'
        root = ET.fromstring(base64.b64decode(assertion))
        for saml2attribute in root.iter('{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
            if saml2attribute.get('Name') == attribute:
                for saml2attributevalue in saml2attribute.iter(attribute_value_urn):
                    return saml2attributevalue.text
        return None