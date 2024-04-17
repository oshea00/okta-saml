""" Config helper """
# Copyright 2024 Michael OShea
from errno import ESTALE
import os
import sys
from configparser import RawConfigParser
from getpass import getpass
import validators


class OktaAuthConfig():
    """ Config helper class """
    def __init__(self, logger):
        self.logger = logger
        self.config_path = os.path.expanduser('~') + '/.okta-saml'
        self._value = RawConfigParser()
        self._value.read(self.config_path)
    
    @staticmethod
    def configure(logger):
        value = RawConfigParser()
        config_path = os.path.expanduser('~') + '/.okta-saml'
        if os.path.exists(config_path):
            value.read(config_path)
            print(f"You have preconfigured Okta profiles: {value.sections()}")
            print(f"This command will append new profile to the existing {config_path} config file")
        else:
            print(f"This command will create a new {config_path} config file")

        confirm = input('Would you like to proceed? [y/n]: ')
        if confirm == 'y':
            logger.info(f"Creating new {config_path} file")
            okta_profile = input('Enter Okta profile name: ')
            if not okta_profile:
                okta_profile = 'default'
            profile = input('Enter credentials profile name: ')
            base_url = input('Enter Okta base url [your main organisation Okta url]: ')
            username = input('Enter Okta username: ')
            app_link = input('Enter OKTA SAML App app-link: ')
            issuer_url = input('Enter issuer-url: ')
            scope = input('Enter scope: ')

            value.add_section(okta_profile)
            value.set(okta_profile, 'base-url', base_url)
            value.set(okta_profile, 'profile', profile)
            value.set(okta_profile, 'username', username)
            value.set(okta_profile, 'issuer', issuer_url)
            value.set(okta_profile, 'scope', scope)
            value.set(okta_profile, 'app-link', app_link)

            with open(config_path, 'w') as configfile:
                value.write(configfile)

            print(f"Configuration {config_path} successfully updated. Now you can authenticate to Okta")
            print(f"Execute 'okta-saml -o {okta_profile} -p {profile}")
            sys.exit(0)
        else:
            sys.exit(0)

    def base_url_for(self, okta_profile):
        """ Gets base URL from config """
        if self._value.has_option(okta_profile, 'base-url'):
            base_url = self._value.get(okta_profile, 'base-url')
            self.logger.info("Authenticating to: %s" % base_url)
        elif self._value.has_option('default', 'base-url'):
            base_url = self._value.get('default', 'base-url')
            self.logger.info(
                "Using base-url from default profile %s" % base_url
            )
        else:
            base_url = input('Enter base-url: ')
        return base_url

    def app_link_for(self, okta_profile):
        """ Gets app_link from config """
        app_link = None
        if self._value.has_option(okta_profile, 'app-link'):
            app_link = self._value.get(okta_profile, 'app-link')
        elif self._value.has_option('default', 'app-link'):
            app_link = self._value.get('default', 'app-link')
        else:
            app_link = input('Enter app-link: ')

        if app_link:
            try:
                if not validators.url(app_link):
                    self.logger.error("The app-link provided: %s is an invalid url" % app_link)
                    sys.exit(-1)
            except TypeError as ex:
                self.logger.error("Malformed string in app link URL. Ensure there are no invalid characters.")
            self.logger.info("App Link set as: %s" % app_link)
            return app_link
        
    def issuer_url_for(self, okta_profile):
        """ Gets app_link from config """
        issuer_url = None
        if self._value.has_option(okta_profile, 'issuer'):
            issuer_url = self._value.get(okta_profile, 'issuer')
        elif self._value.has_option('default', 'issuer'):
            issuer_url = self._value.get('default', 'issuer')
        else:
            issuer_url = input('Enter issuer-url: ')

        if issuer_url:
            try:
                if not validators.url(issuer_url):
                    self.logger.error("The issuer url provided: %s is an invalid url" % issuer_url)
                    sys.exit(-1)
            except TypeError as ex:
                self.logger.error("Malformed string in issuer URL. Ensure there are no invalid characters.")
            self.logger.info("Issuer url set as: %s" % issuer_url)
            return issuer_url
        
    def scope_for(self, okta_profile):
        """ Gets scope from config """
        scope = None
        if self._value.has_option(okta_profile, 'scope'):
            scope = self._value.get(okta_profile, 'scope')
            self.logger.info("Scope set as: %s" % scope)
        elif self._value.has_option('default', 'scope'):
            scope = self._value.get('default', 'scope')
            self.logger.info("Scope set as: %s" % scope)
        else:
            scope = input('Enter scope(s): ')
        return scope


    def username_for(self, okta_profile):
        """ Gets username from config """
        if self._value.has_option(okta_profile, 'username'):
            username = self._value.get(okta_profile, 'username')
            self.logger.info("Authenticating as: %s" % username)
        elif self._value.has_option('default', 'username'):
            username = self._value.get('default', 'username')
            self.logger.info("Authenticating as: %s" % username)
        else:
            username = input('Enter username: ')
        return username

    def password_for(self, okta_profile):
        """ Gets password from config """
        if self._value.has_option(okta_profile, 'password'):
            password = self._value.get(okta_profile, 'password')
        elif self._value.has_option('default', 'password'):
            password = self._value.get('default', 'password')
        else:
            password = getpass('Enter password: ')
        return password

    @staticmethod
    def get_okta_profiles():
        value = RawConfigParser()
        config_path = os.path.expanduser('~') + '/.okta-saml'
        value.read(config_path)
        return value.sections()
