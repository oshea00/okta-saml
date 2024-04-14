""" Wrapper script for radius api which handles Okta auth """
# pylint: disable=C0325,R0913,R0914
# Copyright 2024 Michael OShea
from email.policy import default
import sys
import logging
import click
from oktaradiuscli.version import __version__
from oktaradiuscli.okta_auth import OktaAuth
from oktaradiuscli.okta_auth_config import OktaAuthConfig
from oktaradiuscli.radius_auth import RadiusAuth
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse

def okta_switch(logger):
    okta_profiles = sorted(OktaAuthConfig.get_okta_profiles())
    okta_profile_selected = 0 if len(okta_profiles) == 1 else None
    if okta_profile_selected is None:
        print("Available Okta profiles:")
        for index, profile in enumerate(okta_profiles):
            print("%d: %s" % (index + 1, profile))

        okta_profile_selected = int(input('Please select Okta profile: ')) - 1
        logger.debug(f"Selected {okta_profiles[okta_profile_selected]}")
            
    return okta_profiles[okta_profile_selected]

def get_server_url(full_url):
    parsed_url = urlparse(full_url)
    server_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return server_url

def get_jwt_token(client_id, client_secret, token_url, scope):

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    payload = {
        "grant_type": "client_credentials",
        "scope": scope
    }

    response = requests.post(token_url, auth=HTTPBasicAuth(client_id, client_secret), data=payload, headers=headers)

    jwt_decoded = None

    if response.status_code == 200:
        jwt_json = response.json()
        jwt_decoded = jwt_json['access_token']

    return jwt_decoded

def get_credentials(radius_auth, okta_profile, profile,
                    verbose, logger, totp_token,  
                    okta_username=None, okta_password=None):
    """ Gets credentials from Okta """

    okta_auth_config = OktaAuthConfig(logger)
    okta = OktaAuth(okta_profile, verbose, logger, totp_token, 
        okta_auth_config, okta_username, okta_password)

    _, assertion = okta.get_assertion()

    scope = radius_auth.extract_scope_from(assertion)
    client_id = radius_auth.extract_clientid_from(assertion)
    client_secret = radius_auth.extract_clientsecret_from(assertion)
    app_link = okta_auth_config.app_link_for(okta_profile)
    token_url = f'{get_server_url(app_link)}/oauth2/default/v1/token'

    jwt_token = get_jwt_token(
        client_id,
        client_secret,
        token_url,
        scope
    )

    session_token = jwt_token

    radius_auth.write_jwt_token(session_token)


# pylint: disable=R0913
@click.command()
@click.option('-v', '--verbose', is_flag=True, help='Enables verbose mode')
@click.option('-V', '--version', is_flag=True,help='Outputs version number and sys.exits')
@click.option('-d', '--debug', is_flag=True, help='Enables debug mode')
@click.option('-f', '--force', is_flag=True, help='Forces new credentials.')
@click.option('-o', '--okta-profile', help="Name of the profile to use in .okta-radius. \
If none is provided, then the default profile will be used.\n")
@click.option('-p', '--profile', help="Name of the profile to store temporary \
credentials in ~/.radius/credentials. If profile doesn't exist, it will be \
created. If omitted, credentials will output to console.\n")
@click.option('-t', '--token', help='TOTP token from your authenticator app')
@click.option('-U', '--username', 'okta_username', help="Okta username")
@click.option('-P', '--password', 'okta_password', help="Okta password")
@click.option('--config', is_flag=True, help="Okta config initialization/addition")
@click.option('-s', '--switch', is_flag=True, default=False, is_eager=True, help="Switch to another okta profile and refresh the token")
def main(okta_profile, profile, verbose, version,
         debug, force, 
         token, okta_username, okta_password, config, switch):
    """ Authenticate to radiuscli using Okta """
    if version:
        print(__version__)
        sys.exit(0)

    # Set up logging
    logger = logging.getLogger('okta-radiuscli')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARN)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    if verbose:
        handler.setLevel(logging.INFO)
    if debug:
        handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    if config:
        OktaAuthConfig.configure(logger)

    if not okta_profile:
        okta_profile = "default"
    
    if switch:
        okta_profile = okta_switch(logger)

    radius_auth = RadiusAuth(profile, okta_profile, verbose, logger)
    if force or not radius_auth.check_jwt_token():
        if force and profile:
            logger.info("Force option selected, \
                getting new credentials anyway.")
        get_credentials(
            radius_auth, okta_profile, profile, verbose, logger, token, okta_username, okta_password
        )

if __name__ == "__main__":
    # pylint: disable=E1120
    main()
    # pylint: enable=E1120
