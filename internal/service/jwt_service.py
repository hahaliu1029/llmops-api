import os
from typing import Any
from injector import inject
from dataclasses import dataclass
import jwt


@inject
@dataclass
class JwtService:
    """JWT服务"""

    @classmethod
    def generate_token(cls, payload: dict[str, Any]) -> str:
        """根据传递的载荷信息生成JWT令牌"""
        secret_key = os.getenv("JWT_SECRET_KEY")
        return jwt.encode(payload, secret_key, algorithm="HS256")

    @classmethod
    def parse_token(cls, token: str) -> dict[str, Any]:
        """解析JWT令牌，返回载荷信息"""
        secret_key = os.getenv("JWT_SECRET_KEY")
        try:
            return jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token已过期, 请重新登录")
        except jwt.InvalidTokenError:
            raise ValueError("Token无效，请重新登录")
        except Exception as e:
            raise e
