from urllib import parse

import requests
from .oauth import OAuth, OAuthUserInfo


class GithubOAuth(OAuth):
    """Github OAuth授权认证类"""

    _AUTHORIZE_URL = "https://github.com/login/oauth/authorize"  # 跳转授权接口
    _ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"  # 获取令牌接口
    _USER_INFO_URL = "https://api.github.com/user"  # 获取用户信息接口
    _EMAINL_INFO_URL = "https://api.github.com/user/emails"  # 获取用户邮箱信息接口

    def get_provider(self) -> str:
        return "github"

    def get_authorization_url(self) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email",  # 请求用户邮箱权限
        }
        return f"{self._AUTHORIZE_URL}?{parse.urlencode(params)}"

    def get_access_token(self, code: str) -> str:
        # 组装请求数据
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        headers = {"Accept": "application/json"}

        # 发起请求并获取数据
        response = requests.post(self._ACCESS_TOKEN_URL, data=data, headers=headers)
        response.raise_for_status()
        resp_json = response.json()

        # 提取access_token对应的数据
        access_token = resp_json.get("access_token")

        if not access_token:
            raise ValueError(f"Github OAuth获取access_token失败: {resp_json}")

        return access_token

    def get_raw_user_info(self, token: str) -> dict:
        # 组装请求头
        headers = {
            "Authorization": f"token {token}",
        }

        # 获取用户信息
        response = requests.get(self._USER_INFO_URL, headers=headers)
        response.raise_for_status()
        raw_info = response.json()

        # 获取用户邮箱信息
        email_response = requests.get(
            self._EMAINL_INFO_URL,
            headers=headers,
        )
        # email_response.raise_for_status()
        email_info = email_response.json()

        # 提取邮箱
        primary_email = None

        if primary_email is None:
            primary_email = self._transform_user_info(raw_info)

            print(primary_email)

        return {**raw_info, "email": primary_email.email}

    def _transform_user_info(self, raw_info: dict) -> OAuthUserInfo:
        # 提取邮箱，如果不存在，设置一个默认邮箱
        email = raw_info.get("email")

        if not email:
            email = (
                f"{raw_info.get('id')}{raw_info.get('login')}@user.no-reply@github.com"
            )

        # 组装数据
        return OAuthUserInfo(
            id=str(raw_info.get("id")),
            name=raw_info.get("name"),
            email=email,
        )
