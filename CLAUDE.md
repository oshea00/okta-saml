# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python CLI tool called `okta-saml` that authenticates users against Okta and retrieves temporary JWT credentials for SAML-enabled APIs. The tool performs SAML assertion-based authentication and stores the resulting JWT tokens for API access.

## Architecture

The codebase is organized into the `oktasamlcli` package with the following key modules:

- **okta_samlcli.py**: Main CLI entry point using Click framework. Handles command-line arguments and orchestrates the authentication flow
- **okta_auth.py**: Core Okta authentication logic - handles primary auth, session management, authorization code flow, and JWT token retrieval
- **saml_auth.py**: SAML assertion processing and JWT token management - extracts client credentials from SAML assertions and manages credential storage
- **okta_auth_config.py**: Configuration management for Okta profiles from `~/.okta-saml` file

### Authentication Flow

The application follows this flow:
1. Authenticate with Okta using username/password
2. Retrieve SAML assertion from configured app link
3. Extract ClientID and ClientSecret from SAML assertion attributes
4. Perform OAuth2 authorization code flow
5. Obtain JWT access token
6. Store credentials in `~/.saml/credentials` or output to console

## Development Commands

### Installation
```bash
python3 -m pip install . --upgrade
```

### Running the CLI
```bash
okta-saml --profile <profile_name>
```

### Configuration
```bash
okta-saml --config  # Initialize new Okta profile configuration
```

## Dependencies

This project uses:
- **requests**: HTTP client for Okta API calls
- **click**: CLI framework for command-line interface
- **beautifulsoup4**: HTML/XML parsing for SAML responses
- **ConfigParser**: Configuration file management
- **validators**: Input validation

## Configuration Files

- **~/.okta-saml**: Main configuration file containing Okta profiles with base-url, app-link, username, etc.
- **~/.saml/credentials**: Stored JWT credentials organized by profile
- **pyproject.toml**: Python packaging configuration using setuptools
- **requirements.txt**: Python dependencies

## Key Classes and Methods

- `OktaAuth.get_assertion()`: Retrieves SAML assertion from Okta
- `OktaAuth.get_auth_code()`: Performs OAuth2 authorization code flow
- `OktaAuth.get_jwt_token()`: Exchanges auth code for JWT access token
- `SamlAuth.extract_clientid_from()`: Extracts client ID from SAML assertion
- `SamlAuth.check_jwt_token()`: Validates existing JWT token expiration
- `SamlAuth.write_jwt_token()`: Stores JWT token to credentials file

## Security Considerations

The application handles sensitive authentication data including:
- Okta user credentials (optionally stored in config)
- JWT access tokens (stored in ~/.saml/credentials)
- Client secrets from SAML assertions
- Session tokens during authentication flow