from dataclasses import dataclass
from flask import Flask, Blueprint
from injector import inject
from internal.handler import AppHandler


@inject
@dataclass
class Router:
    """路由"""

    app_handler: AppHandler

    def register_router(self, app: Flask):
        """注册路由"""
        # 1. 创建一个蓝图
        blueprint = Blueprint("llmops", __name__, url_prefix="/")

        # 2. 将url与对应控制器方法绑定
        # blueprint.add_url_rule("/ping", view_func=self.app_handler.ping)
        blueprint.add_url_rule(
            "/apps/<uuid:app_id>/debug",
            methods=["POST"],
            view_func=self.app_handler.debug,
        )
        # blueprint.add_url_rule(
        #     "/app", methods=["POST"], view_func=self.app_handler.create_app
        # )

        # blueprint.add_url_rule(
        #     "/app/<uuid:id>", methods=["GET"], view_func=self.app_handler.get_app
        # )

        # blueprint.add_url_rule(
        #     "/app/<uuid:id>", methods=["POST"], view_func=self.app_handler.update_app
        # )

        # blueprint.add_url_rule(
        #     "/app/<uuid:id>/delete",
        #     methods=["POST"],
        #     view_func=self.app_handler.delete_app,
        # )

        # 3. 注册蓝图
        app.register_blueprint(blueprint)
