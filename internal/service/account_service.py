from uuid import UUID
from injector import inject
from dataclasses import dataclass
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy

from internal.model import Account, AccountOAuth


@inject
@dataclass
class AccountService(BaseService):
    """账户服务"""

    db: SQLAlchemy

    def get_account(self, account_id: UUID) -> Account:
        """根据账户ID获取账户信息"""
        return self.get(Account, account_id)

    def get_account_oauth_by_provider_name_and_openid(
        self, provider_name: str, openid: str
    ) -> AccountOAuth:
        """根据提供商名称和openid获取账户OAuth信息"""
        return (
            self.db.session.query(AccountOAuth)
            .filter(
                AccountOAuth.provider == provider_name, AccountOAuth.openid == openid
            )
            .one_or_none()
        )

    def get_account_by_email(self, email: str) -> Account:
        """根据邮箱获取账户信息"""
        return (
            self.db.session.query(Account).filter(Account.email == email).one_or_none()
        )

    def create_account(self, **kwargs) -> Account:
        """根据传递的键值对创建账号信息"""
        return self.create(Account, **kwargs)
