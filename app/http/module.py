from flask_sqlalchemy import SQLAlchemy
from injector import Binder, Module

from internal.extention.database_extension import db


class ExtentionModule(Module):
    """扩展模块"""

    def configure(self, binder: Binder) -> None:
        binder.bind(SQLAlchemy, to=db)
