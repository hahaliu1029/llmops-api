from dataclasses import dataclass
from flask import Flask, Blueprint
from injector import inject
from internal.handler import AppHandler, BuiltinToolHandler, ApiToolHandler


@inject
@dataclass
class Router:
    """路由"""

    app_handler: AppHandler
    builtin_tool_handler: BuiltinToolHandler
    api_tool_handler: ApiToolHandler

    def register_router(self, app: Flask):
        """注册路由"""
        # 1. 创建一个蓝图
        blueprint = Blueprint("llmops", __name__, url_prefix="/")

        # 2. 将url与对应控制器方法绑定
        blueprint.add_url_rule("/ping", view_func=self.app_handler.ping)
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

        # 内置插件广场模块
        blueprint.add_url_rule(
            "/builtin-tools", view_func=self.builtin_tool_handler.get_builtin_tools
        )

        blueprint.add_url_rule(
            "/builtin-tools/<string:provider_name>/tools/<string:tool_name>",
            view_func=self.builtin_tool_handler.get_provider_tool,
        )

        blueprint.add_url_rule(
            "/builtin-tools/<string:provider_name>/icon",
            view_func=self.builtin_tool_handler.get_provider_icon,
        )

        blueprint.add_url_rule(
            "/builtin-tools/categories",
            view_func=self.builtin_tool_handler.get_categories,
        )

        # 自定义API插件模块
        blueprint.add_url_rule(
            "/api-tools/validate-openapi-schema",
            methods=["POST"],
            view_func=self.api_tool_handler.validate_openapi_schema,
        )

        blueprint.add_url_rule(
            "/api-tools",
            methods=["POST"],
            view_func=self.api_tool_handler.create_api_tool,
        )

        # 3. 注册蓝图
        app.register_blueprint(blueprint)
