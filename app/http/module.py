from injector import Binder, Module
from flask_migrate import Migrate

from internal.extension.database_extension import db
from internal.extension.migrate_extention import migrate
from internal.extension.redis_extension import redis_client
from pkg.sqlalchemy import SQLAlchemy
from redis import Redis
from injector import Injector
from flask_login import LoginManager
from internal.extension.login_extension import login_manager


class ExtentionModule(Module):
    """扩展模块"""

    def configure(self, binder: Binder) -> None:
        binder.bind(SQLAlchemy, to=db)
        binder.bind(Migrate, to=migrate)
        binder.bind(Redis, to=redis_client)
        binder.bind(LoginManager, to=login_manager)


injector = Injector([ExtentionModule])
