from pydantic import BaseModel, field_validator
from internal.exception import FailException


class CategoryEntity(BaseModel):
    """内置工具分类实体"""

    category: str  # 分类唯一标识
    name: str  # 分类名称
    icon: str  # 分类图标

    @field_validator("icon")
    def check_icon_extension(cls, value: str):
        """校验icon的后缀是不是svg，如果不是则抛出异常"""
        if not value.endswith(".svg"):
            raise FailException("分类图标必须是svg格式")
        return value
