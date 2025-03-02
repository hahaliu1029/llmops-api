from datetime import datetime, timedelta
import os
from typing import Any
from injector import inject
from dataclasses import dataclass
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
from pkg.oauth import OAuth, GithubOAuth
from internal.exception import NotFoundException
from .account_service import AccountService
from internal.model import AccountOAuth
from flask import request
from .jwt_service import JwtService


@inject
@dataclass
class OAuthService(BaseService):
    """第三方授权认证服务"""

    db: SQLAlchemy
    account_service: AccountService
    jwt_service: JwtService

    @classmethod
    def get_all_oauth(cls) -> dict[str, OAuth]:
        """获取所有第三方授权信息"""
        # 实例化集成的第三方授权类
        github = GithubOAuth(
            client_id=os.getenv("GITHUB_CLIENT_ID"),
            client_secret=os.getenv("GITHUB_CLIENT_SECRET"),
            redirect_uri=os.getenv("GITHUB_REDIRECT_URI"),
        )

        # 构建字典并返回
        return {"github": github}

    @classmethod
    def get_oauth_by_provider_name(cls, provider_name: str) -> OAuth:
        """根据提供商名称获取对应的第三方授权类"""
        oauths = cls.get_all_oauth()
        oauth = oauths.get(provider_name)
        if oauth is None:
            raise NotFoundException(f"未找到提供商名称为{provider_name}的第三方授权")
        return oauth

    def oauth_login(self, provider_name: str, code: str) -> dict[str, Any]:
        """第三方OAuth授权登录, 返回授权凭证以及过期时间"""
        # 根据provider_name获取oauth
        oauth = self.get_oauth_by_provider_name(provider_name)

        # 根据code从第三方登录服务中获取access_token
        oauth_access_token = oauth.get_access_token(code)
        print("1111111111111111111")
        print(oauth_access_token)

        # 根据获取到的token提取user_info信息
        oauth_user_info = oauth.get_user_info(oauth_access_token)

        # 根据provider_name和openid获取授权记录
        account_oauth = (
            self.account_service.get_account_oauth_by_provider_name_and_openid(
                provider_name, oauth_user_info.id
            )
        )

        if not account_oauth:
            # 该授权认证方式是第一次登录，查询邮箱是否存在
            account = self.account_service.get_account_by_email(oauth_user_info.email)
            if not account:
                # 该邮箱未注册，创建新账户
                account = self.account_service.create_account(
                    name=oauth_user_info.name, email=oauth_user_info.email
                )

            # 添加授权认证记录
            account_oauth = self.create(
                AccountOAuth,
                account_id=account.id,
                provider=provider_name,
                openid=oauth_user_info.id,
                encrypted_token=oauth_access_token,
            )
        else:
            # 查找账号信息
            account = self.account_service.get_account(account_oauth.account_id)

        # 更新账号信息，涵盖最后登录时间和IP
        self.update(
            account, last_login_at=datetime.now(), last_login_ip=request.remote_addr
        )
        self.update(account_oauth, encrypted_token=oauth_access_token)

        # 生成授权凭证信息
        expire_at = int((datetime.now() + timedelta(days=30)).timestamp())
        payload = {
            "sub": str(account.id),  # 用户ID
            "iss": "llmops",  # 签发者
            "exp": expire_at,  # 过期时间
        }
        access_token = self.jwt_service.generate_token(payload)

        return {"access_token": access_token, "expire_at": expire_at}
