import uuid
from dataclasses import dataclass
from injector import inject

from internal.model import App
from pkg.sqlalchemy import SQLAlchemy


@inject
@dataclass
class AppService:
    """应用服务逻辑"""

    db: SQLAlchemy

    def create_app(self) -> App:
        """创建应用"""
        with self.db.auto_commit():
            # 1. 创建应用的实例
            app = App(
                name="测试机器人",
                account_id=uuid.uuid4(),
                icon="",
                description="这是一个测试机器人",
            )
            # 2. 添加session会话中
            self.db.session.add(app)
        return app  # 返回创建的应用实例

    def get_app(self, id: uuid.UUID) -> App:
        """获取应用"""
        app = self.db.session.query(App).get(id)
        return app

    def update_app(self, id: uuid.UUID) -> App:
        """更新应用"""
        with self.db.auto_commit():
            app = self.get_app(id)
            app.name = "更新测试机器人" + str(uuid.uuid4())
        return app

    def delete_app(self, id: uuid.UUID) -> App:
        """删除应用"""
        with self.db.auto_commit():
            app = self.get_app(id)
            self.db.session.delete(app)
        return app
