import os

import requests

from iam.exceptions import LoginError

OKTA_DOMAIN = os.environ.get('OKTA_BASE_URL')
if not OKTA_DOMAIN:
    OKTA_DOMAIN = 'https://trial-9818147.okta.com/oauth2/default/v1'

OKTA_CLIENT_ID = os.environ.get('OKTA_CLIENT_ID')
if not OKTA_CLIENT_ID:
    OKTA_CLIENT_ID = '0oa47zdlpcfMYLXeb697'

OKTA_CLIENT_SECRET = os.environ.get('OKTA_CLIENT_SECRET')
if not OKTA_CLIENT_SECRET:
    OKTA_CLIENT_SECRET = 'AQxBks35YR_90s6lPXTW9ZsizjhbWznOMkUe85_-'


class OktaUserInfo:
    def __init__(self, sub, name, locale, email,
                 preferred_username, given_name,
                 family_name, zoneinfo, email_verified):
        """'sub' is the key returned by the OKTA API,
        and these keys corresponds to the keys in the JSON returned by the OKTA API"""
        self.sub = sub
        self.name = name
        self.locale = locale
        self.email = email
        self.preferred_username = preferred_username
        self.given_name = given_name
        self.family_name = family_name
        self.zoneinfo = zoneinfo
        self.email_verified = email_verified


def get_token_by_code(code: str, redirect_uri: str):
    """code: The OAuth 2 Authorization server may not directly return an Access Token after the Resource Owner has
    authorized access. Instead, and for better security, an Authorization Code may be returned, which is then
    exchanged for an Access Token """
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': OKTA_CLIENT_ID,
        'client_secret': OKTA_CLIENT_SECRET
    }
    response = requests.post(f'{OKTA_DOMAIN}/token', headers=headers, data=data)

    if response.status_code == 200:
        response_data = response.json()
        return response_data['access_token']
    else:
        raise LoginError(f'get_user_info: Failed to get access token, {response.content}')


def get_user_info(access_token: str):
    """get user info though access_token"""
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
        'authorization': f'Bearer {access_token}'
    }

    response = requests.get(f'{OKTA_DOMAIN}/userinfo', headers=headers)
    if response.status_code != 200:
        raise LoginError(f'Failed to authenticate user, {response.content}')
    return response.json()
