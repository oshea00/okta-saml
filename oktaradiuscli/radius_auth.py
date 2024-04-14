""" Radius authentication """
# pylint: disable=C0325
# Copyright 2024 Michael OShea
import os
import sys
import base64
import xml.etree.ElementTree as ET
from collections import namedtuple
from configparser import RawConfigParser
from enum import Enum
from subprocess import call

class RadiusAuth():
    """ Methods to support Radius api authentication using jwt """

    def __init__(self, profile, okta_profile, verbose, logger):
        home_dir = os.path.expanduser('~')
        shared_credentials_file = os.getenv("RADIUS_SHARED_CREDENTIALS_FILE")
        if shared_credentials_file:
            self.creds_dir = os.path.dirname(shared_credentials_file)
            self.creds_file = shared_credentials_file
        else:
            self.creds_dir = home_dir + "/.radius"
            self.creds_file = self.creds_dir + "/credentials"
        self.profile = profile
        self.verbose = verbose
        self.logger = logger
        self.role = ""
        
        okta_config = home_dir + '/.okta-radius'
        parser = RawConfigParser()
        parser.read(okta_config)

        if parser.has_option(okta_profile, 'profile') and not profile:
            self.profile = parser.get(okta_profile, 'profile')
            self.logger.debug("Setting radius profile to %s" % self.profile)

    def set_default_profile(self, parser: RawConfigParser):
        if not parser.has_section('default'):
            parser.add_section('default')
        for key, value in parser.items(self.profile):
            parser.set('default', key, value)
        self.logger.info("Setting default profile.")
        with open(self.creds_file, 'w+') as configfile:
            parser.write(configfile)

    def check_jwt_token(self):
        """ Verifies that jwt is valid """
        # Don't check for creds if profile is blank
        if not self.profile:
            return False

        parser = RawConfigParser()
        parser.read(self.creds_file)

        if not os.path.exists(self.creds_dir):
            self.logger.info("AWS credentials path does not exist. Not checking.")
            return False

        elif not os.path.isfile(self.creds_file):
            self.logger.info("Radius credentials file does not exist. Not checking.")
            return False

        elif not parser.has_section(self.profile):
            self.logger.info("No existing credentials found. Requesting new credentials.")
            return False

        self.logger.info("Radius credentials are valid. Nothing to do.")
        RadiusAuth.set_default_profile(self, parser)

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
            RadiusAuth.set_default_profile(self, config)

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

