from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class ToolParamType(str, Enum):
    """工具参数类型枚举"""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    SELECT = "select"


class ToolParam(BaseModel):
    """工具参数类型"""

    name: str  # 参数实际名字
    label: str  # 参数标签
    type: ToolParamType  # 参数类型
    required: bool = False  # 是否必填
    default: Optional[Any] = None  # 默认值
    min: Optional[float] = None  # 最小值
    max: Optional[float] = None  # 最大值
    options: list[dict[str, Any]] = Field(default_factory=list)  # 选项


class ToolEntity(BaseModel):
    """工具实体, 映射数据为工具名字对应的yaml文件"""

    name: str  # 工具名字
    label: str  # 工具标签
    description: str  # 工具描述
    params: list[ToolParam] = Field(default_factory=list)  # 工具参数
