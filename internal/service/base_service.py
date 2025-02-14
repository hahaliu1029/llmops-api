from typing import Any, Optional
from pkg.sqlalchemy import SQLAlchemy
from internal.exception import FailException


class BaseService:
    """基础服务, 完善数据库的增删改查功能，简化代码"""

    db: SQLAlchemy

    def create(self, model: Any, **kwargs: Any) -> Any:
        """根据模型创建数据"""
        with self.db.auto_commit():
            model_instance = model(**kwargs)
            self.db.session.add(model_instance)

        return model_instance

    def delete(self, model_instance: Any) -> Any:
        """删除数据"""
        with self.db.auto_commit():
            self.db.session.delete(model_instance)

        return model_instance

    def update(self, model_instance: Any, **kwargs: Any) -> Any:
        """更新数据"""
        with self.db.auto_commit():
            for filed, value in kwargs.items():
                if hasattr(model_instance, filed):
                    setattr(model_instance, filed, value)
                else:
                    raise FailException(f"模型{model_instance}中不存在字段{filed}")

        return model_instance

    def get(self, model: Any, primary_key: Any) -> Optional[Any]:
        """根据主键获取数据"""
        return self.db.session.query(model).get(primary_key)
