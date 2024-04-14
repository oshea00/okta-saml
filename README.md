# okta-saml - Retrieve Saml-Enabled API credentials from Okta

Authenticates a user against Okta and then uses the resulting SAML assertion to retrieve temporary credentials for saml-enabled APIs.

when the command line is run with desired arguments (described below), upon successful login, the attributes in the SAML assertion will be used obtain a jwt token for the associated API and scope.

## Required OKTA Setup

Create a SAML App integration with default settings. Add attributes to the SAML definition for ClientID and ClientSecret, and the desired Scope in the Audience. These should contain the values from the client credential flow application you want to associate with your API's auth server and related Scope. Create scope in your auth server as-needed.

The embed link on your SAML app will be used for the app-link value in your ~/.okta-saml file.

Associate your users/groups in the authserver access policies as-needed - one of those must include the intermediary client credential flow app that your saml attributes refer to.

## Disclaimer
Okta is a registered trademark of Okta, Inc. and this tool has no affiliation with or sponsorship by Okta, Inc.

## Installation
- `> python3 -m pip install . --upgrade`
- Execute `okta-saml --config` and follow the steps to configure your Okta profile OR
- Configure okta-saml via the `~/.okta-saml` file with the following parameters:

```
[default]
base-url = <your_okta_org>.okta.com
app-link = <app_link_from_okta> # Found in Okta's configuration for your SAML Application link.
profile  = <saml_profile_to_store_credentials> # Sets your temporary credentials to a profile in `.saml/credentials`. Overridden by `--profile` command line flag

## The remaining parameters are optional.
## You may be prompted for them, if they're not included here.
username = <your_okta_username>
password = <your_okta_password> # Only save your password if you know what you are doing!
```

## Usage

`okta-saml --profile <saml_profile>`
- Subsequent executions will first check if the credentials are still valid and skip Okta authentication if so.
- Multiple Okta profiles are supported, but if none are specified, then `default` will be used.
- Selections for saml api are saved to the `~/.okta-saml` file. 

### Example

`okta-saml --profile default`

Optional flags:
- `--profile` or `-p` Sets your temporary credentials to a profile in `.saml/credentials`. If omitted and not configured in `~/.okta-saml`, credentials will output to console.
- `--username` or `-U` Okta username.
- `--password` or `-P` Okta password.
- `--force` or `-f` Ignores result of JWT expiration check and gets new credentials from OKTA. Used in conjunction with `--profile`.
- `--verbose` or `-v` More verbose output.
- `--debug` or `-d` Very verbose output. Useful for debugging.
- `--cache` or `-c` Cache the acquired credentials to ~/.okta-credentials.cache (only if --profile is unspecified)
- `--okta-profile` or `-o` Use a Okta profile, other than `default` in `.okta-saml`. Useful for multiple Okta tenants.
- `--config` Add/Create new Okta profile configuration.
- `--version` or `-V` Outputs version number then exits.

