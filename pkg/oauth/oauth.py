from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class OAuthUserInfo:
    """OAuth用户基础信息，只记录id/name/email"""

    id: str
    name: str
    email: str


@dataclass
class OAuth(ABC):
    """第三方OAuth授权认证基础类"""

    client_id: str  # 客户端id
    client_secret: str  # 客户端密钥
    redirect_uri: str  # 重定向地址

    @abstractmethod
    def get_provider(self) -> str:
        """获取OAuth提供商"""
        pass

    @abstractmethod
    def get_authorization_url(self) -> str:
        """获取OAuth授权地址"""
        pass

    @abstractmethod
    def get_access_token(self, code: str) -> str:
        """获取OAuth令牌"""
        pass

    @abstractmethod
    def get_raw_user_info(self, token: str) -> dict:
        """获取OAuth用户原始信息"""
        pass

    def get_user_info(self, token: str) -> OAuthUserInfo:
        """获取OAuth用户OAuthUserInfo信息"""
        raw_info = self.get_raw_user_info(token)
        return self._transform_user_info(raw_info)

    @abstractmethod
    def _transform_user_info(self, raw_info: dict) -> OAuthUserInfo:
        """转换用户原始信息为OAuthUserInfo"""
        pass
