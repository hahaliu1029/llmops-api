from typing import Optional
from injector import inject
from dataclasses import dataclass
from flask import Request

from internal.model import Account
from internal.exception import UnauthorizedException
from internal.service import JwtService, AccountService


@inject
@dataclass
class Middleware:
    """应用中间件,可以重写request_loader与unauthorized_handler"""

    jwt_service: JwtService
    account_service: AccountService

    def request_loader(self, request: Request) -> Optional[Account]:
        """登录管理器的请求加载器"""
        # 为llmops路由蓝图创建请求加载器
        if request.blueprint == "llmops":
            # 提取请求头
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise UnauthorizedException("该接口需要授权才能访问，请先登录")

            # 请求信息中没有空格分隔符，则验证失败
            if " " not in auth_header:
                raise UnauthorizedException(
                    "该接口需要授权才能访问，验证格式失败，请先登录"
                )

            # 分割授权信息，必须符合Bearer access_token格式
            auth_schema, access_token = auth_header.split(None, 1)
            if auth_schema.lower() != "bearer":
                raise UnauthorizedException(
                    "该接口需要授权才能访问，验证格式失败，请先登录"
                )

            # 解析token得到用户信息
            payload = self.jwt_service.parse_token(access_token)
            account_id = payload.get("sub")
            return self.account_service.get_account(account_id)

        else:
            return None
