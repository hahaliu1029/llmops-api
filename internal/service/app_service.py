import uuid
from dataclasses import dataclass
from injector import inject
from flask_sqlalchemy import SQLAlchemy

from internal.model import App


@inject
@dataclass
class AppService:
    """应用服务逻辑"""

    db: SQLAlchemy

    def create_app(self) -> App:
        """创建应用"""
        # 1. 创建应用的实例
        app = App(
            name="测试机器人",
            account_id=uuid.uuid4(),
            icon="",
            description="这是一个测试机器人",
        )
        # 2. 添加session会话中
        self.db.session.add(app)
        # 3. 提交
        self.db.session.commit()
        return app  # 返回创建的应用实例
