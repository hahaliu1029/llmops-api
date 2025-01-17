from injector import Binder, Module
from flask_migrate import Migrate

from internal.extention.database_extension import db
from internal.extention.migrate_extention import migrate
from pkg.sqlalchemy import SQLAlchemy


class ExtentionModule(Module):
    """扩展模块"""

    def configure(self, binder: Binder) -> None:
        binder.bind(SQLAlchemy, to=db)
        binder.bind(Migrate, to=migrate)
