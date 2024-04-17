""" Wrapper script for saml api which handles Okta auth """
# pylint: disable=C0325,R0913,R0914
# Copyright 2024 Michael OShea
import sys
import logging
import click
from oktasamlcli.version import __version__
from oktasamlcli.okta_auth import OktaAuth
from oktasamlcli.okta_auth_config import OktaAuthConfig
from oktasamlcli.saml_auth import SamlAuth

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

def get_credentials(saml_auth, okta_profile, profile,
                    verbose, logger,   
                    okta_username=None, okta_password=None):
    """ Gets credentials from Okta """

    okta_auth_config = OktaAuthConfig(logger)
    okta = OktaAuth(okta_profile, verbose, logger, 
        okta_auth_config, okta_username, okta_password)

    _, assertion = okta.get_assertion()

    client_id = saml_auth.extract_clientid_from(assertion)
    client_secret = saml_auth.extract_clientsecret_from(assertion)

    okta.get_auth_code(client_id)

    okta.get_jwt_token(
        client_id,
        client_secret
    )

    saml_auth.write_jwt_token(okta.access_token)


# pylint: disable=R0913
@click.command()
@click.option('-v', '--verbose', is_flag=True, help='Enables verbose mode')
@click.option('-V', '--version', is_flag=True,help='Outputs version number and sys.exits')
@click.option('-d', '--debug', is_flag=True, help='Enables debug mode')
@click.option('-f', '--force', is_flag=True, help='Forces new credentials.')
@click.option('-o', '--okta-profile', help="Name of the profile to use in .okta-saml. \
If none is provided, then the default profile will be used.\n")
@click.option('-p', '--profile', help="Name of the profile to store temporary \
credentials in ~/.saml/credentials. If profile doesn't exist, it will be \
created. If omitted, credentials will output to console.\n")
@click.option('-U', '--username', 'okta_username', help="Okta username")
@click.option('-P', '--password', 'okta_password', help="Okta password")
@click.option('--config', is_flag=True, help="Okta config initialization/addition")
@click.option('-s', '--switch', is_flag=True, default=False, is_eager=True, help="Switch to another okta profile and refresh the token")
def main(okta_profile, profile, verbose, version,
         debug, force, 
         okta_username, okta_password, config, switch):
    """ Authenticate to saml using Okta """
    if version:
        print(__version__)
        sys.exit(0)    

    # Set up logging
    logger = logging.getLogger('okta-saml')
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

    saml_auth = SamlAuth(profile, okta_profile, verbose, logger)
    if force or not saml_auth.check_jwt_token():
        if force and profile:
            logger.info("Force option selected, \
                getting new credentials anyway.")
        get_credentials(
            saml_auth, okta_profile, profile, verbose, logger, okta_username, okta_password
        )

if __name__ == "__main__":
    # pylint: disable=E1120
    main()
    # pylint: enable=E1120
