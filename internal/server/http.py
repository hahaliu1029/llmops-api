import logging
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_login import LoginManager

from internal.exception.exception import CustomException
from internal.router import Router
from internal.extension import logging_extension, redis_extension, celery_extension
from config import Config

from pkg.response.http_code import HttpCode
from pkg.sqlalchemy import SQLAlchemy
from internal.model.app import App
from internal.middleware import Middleware


class Http(Flask):
    """http服务"""

    def __init__(
        self,
        *args,
        conf: Config,
        db: SQLAlchemy,
        migrate: Migrate,
        middleware: Middleware,
        login_manager: LoginManager,
        router: Router,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        print("Http init")

        # 配置
        self.config.from_object(conf)

        self.register_error_handler(Exception, self._register_error_handler)

        # 注册数据库
        db.init_app(self)
        migrate.init_app(self, db, directory="internal/migration")
        logging_extension.init_app(self)
        redis_extension.init_app(self)
        celery_extension.init_app(self)
        login_manager.init_app(self)
        # with self.app_context():  # 创建上下文
        #     _ = App()
        #     db.create_all()

        # 注册路由
        CORS(
            self,
            resources={r"/*": {"origins": "*"}},
            supports_credentials=True,
        )

        # 注册中间件
        login_manager.request_loader(middleware.request_loader)

        router.register_router(self)

    def _register_error_handler(self, error: Exception):
        """注册异常处理"""

        # 日志记录异常信息
        logging.error("An error occurred: %s", error, exc_info=True)

        # 1. 获取异常信息， 如果是自定义异常，获取code和message等信息
        if isinstance(error, CustomException):
            return (
                jsonify(
                    {
                        "code": error.code,
                        "message": error.message,
                        "data": error.data or {},
                    }
                ),
                200,
            )
        # 2. 如果不是自定义异常，则有可能是程序 数据库等异常，也需要处理
        if self.debug or self.testing or os.getenv("FLASK_ENV") == "development":
            raise error
        else:
            return (
                jsonify({"code": HttpCode.FAIL, "message": str(error), "data": {}}),
                200,
            )
