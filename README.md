# okta-radiuscli - Retrieve Radius API credentials from Okta

Authenticates a user against Okta and then uses the resulting SAML assertion to retrieve temporary credentials for radius APIs.

Parsing the HTML is still required to get the SAML assertion, after authentication is complete. However, since we only need to look for the SAML assertion in a single, predictable tag, `<input name="SAMLResponse"...`, the results are a lot more stable across any changes that Okta may make to their interface.

when the command line is run with desired arguments (described below), upon successful login, the attributes in the SAML assertion will be used obtain a jwt token for the associated API scope.

## Required OKTA Setup

Create a SAML App integration with default settings. Add attributes to the SAML definition for ClientID and ClientSecret. These should contain the values from the client credential flow application you want to associate with your API's auth server. Create one or more scopes in your auth server as-needed.

The embed link on your SAML app will be used for the app-link value in your ~/.okta-radius file.

Associate your users/groups in the authserver access policies as-needed - one of those must include the intermediary client credential flow app that your saml attributes refer to.

## Disclaimer
Okta is a registered trademark of Okta, Inc. and this tool has no affiliation with or sponsorship by Okta, Inc.

## Python Support
This project is written for Python 3. Running it with Python 2 may work, but it is not supported. Since Python 2 is end-of-life (as of 2020-JAN-01), feature requests and PRs to add Python 2 support will likely not be accepted, outside of extreme circumstances.

## Installation
- `> python3 -m pip install . --upgrade`
- Execute `okta-radiuscli --config` and follow the steps to configure your Okta profile OR
- Configure okta-radiuscli via the `~/.okta-radius` file with the following parameters:

```
[default]
base-url = <your_okta_org>.okta.com
app-link = <app_link_from_okta> # Found in Okta's configuration for your AWS account.
scope = scope to use for API auth server
profile  = <radius_profile_to_store_credentials> # Sets your temporary credentials to a profile in `.radius/credentials`. Overridden by `--profile` command line flag

## The remaining parameters are optional.
## You may be prompted for them, if they're not included here.
username = <your_okta_username>
password = <your_okta_password> # Only save your password if you know what you are doing!
duration = 3600 # duration in seconds to request a session token for. default: 3600
```

## Usage

`okta-radiuscli --profile <radius_profile>`
- Subsequent executions will first check if the credentials are still valid and skip Okta authentication if so.
- Multiple Okta profiles are supported, but if none are specified, then `default` will be used.
- Selections for radius api and radius scope are saved to the `~/.okta-radius` file. 

### Example

`okta-radiuscli --profile my-radius-account`

If no awscli commands are provided, then okta-radiuscli will simply output STS credentials to your credentials file, or console, depending on how `--profile` is set.

Optional flags:
- `--profile` or `-p` Sets your temporary credentials to a profile in `.radius/credentials`. If omitted and not configured in `~/.okta-radius`, credentials will output to console.
- `--username` or `-U` Okta username.
- `--password` or `-P` Okta password.
- `--force` or `-f` Ignores result of STS credentials validation and gets new credentials from OKTA. Used in conjunction with `--profile`.
- `--verbose` or `-v` More verbose output.
- `--debug` or `-d` Very verbose output. Useful for debugging.
- `--cache` or `-c` Cache the acquired credentials to ~/.okta-credentials.cache (only if --profile is unspecified)
- `--okta-profile` or `-o` Use a Okta profile, other than `default` in `.okta-radius`. Useful for multiple Okta tenants.
- `--token` or `-t` Pass in the TOTP token from your authenticator
- `--config` Add/Create new Okta profile configuration.
- `--version` or `-V` Outputs version number then exits.

## Run from docker container
This process is taken from gimme-aws-creds and adapted

### Build the image 
```
docker build -t okta-radiuscli .

```
### Run the image with the command

```
docker run -it --rm -v ~/.radius/credentials:/root/.radius/credentials -v ~/.okta-radiuscli:/root/.okta-radius --profile default okta-radiuscli
```

