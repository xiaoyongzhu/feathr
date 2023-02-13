import requests


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


def get_user_info(access_token: str):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
        'authorization': f'Bearer {access_token}'
    }

    response = requests.get(f'https://trial-9818147.okta.com/oauth2/default/v1/userinfo', headers=headers)
    if response.status_code != 200:
        raise Exception('Failed to authenticate user')
    return response.json()
