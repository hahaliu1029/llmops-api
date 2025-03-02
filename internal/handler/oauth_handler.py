from injector import inject
from dataclasses import dataclass
from internal.service import OAuthService
from pkg.response import success_json, validate_error_json
from internal.schema.oauth_schema import AuthorizeReq, AuthorizeResp


@inject
@dataclass
class OAuthHandler:
    """第三方授权认证处理器"""

    oauth_service: OAuthService

    def provider(self, provider_name: str):
        """根据提供商名称获取对应的手群认证重定向地址"""
        # 根据provider_name获取对应的第三方授权类
        oauth = self.oauth_service.get_oauth_by_provider_name(provider_name)

        # 调用函数获取授权地址
        redirect_url = oauth.get_authorization_url()

        return success_json(data={"redirect_url": redirect_url})

    def authorize(self, provider_name: str):
        """根据提供商名称+code获取对应的第三方授权信息"""
        # 提取请求数据并校验
        req = AuthorizeReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务登录账号
        credential = self.oauth_service.oauth_login(provider_name, req.code.data)

        # 返回授权凭证
        return success_json(AuthorizeResp().dump(credential))
