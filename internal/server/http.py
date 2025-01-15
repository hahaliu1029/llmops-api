from flask import Flask, request, jsonify
from internal.router import Router
from config import Config


class Http(Flask):
    """http服务"""

    def __init__(self, *args, conf: Config, router: Router, **kwargs):
        super().__init__(*args, **kwargs)
        # 注册路由
        router.register_router(self)

        # 配置
        self.config.from_object(conf)
