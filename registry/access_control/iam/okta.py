import os

import requests

from iam.exceptions import LoginError

okta_domain = os.environ.get('OKTA_BASE_URL')
if okta_domain is None:
    okta_domain = 'https://trial-9818147.okta.com/oauth2/default/v1'

okta_client_id = os.environ.get('OKTA_CLIENT_ID')
if okta_client_id is None:
    okta_client_id = '0oa47zdlpcfMYLXeb697'

okta_client_secret = os.environ.get('OKTA_CLIENT_SECRET')
if okta_client_secret is None:
    okta_client_secret = 'AQxBks35YR_90s6lPXTW9ZsizjhbWznOMkUe85_-'


class OkataUserInfo:
    def __init__(self, sub, name, locale, email,
                 preferred_username, given_name,
                 family_name, zoneinfo, email_verified):
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
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': okta_client_id,
        'client_secret': okta_client_secret
    }
    response = requests.post(f'{okta_domain}/token', headers=headers, data=data)

    if response.status_code == 200:
        response_data = response.json()
        return response_data['access_token']
    else:
        raise LoginError(f'Failed to get access token, {response.content}')


def get_user_info(access_token: str):
    """get user info though access_token"""
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
        'authorization': f'Bearer {access_token}'
    }

    response = requests.get(f'{okta_domain}/userinfo', headers=headers)
    if response.status_code != 200:
        raise LoginError(f'Failed to authenticate user, {response.content}')
    return response.json()
