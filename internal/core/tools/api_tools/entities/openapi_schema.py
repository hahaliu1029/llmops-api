from enum import Enum
from pydantic import BaseModel, Field, field_validator
from internal.exception import ValidateErrorException


class ParameterType(str, Enum):
    """参数支持的类型"""

    STR: str = "str"
    INT: str = "int"
    FLOAT: str = "float"
    BOOL: str = "bool"


class ParameterIn(str, Enum):
    """参数支持存放的位置"""

    PATH: str = "path"
    QUERY: str = "query"
    HEADER: str = "header"
    COOKIE: str = "cookie"
    REQUEST_BODY: str = "request_body"


class OpenAPISchema(BaseModel):
    """OpenAPI规范的数据结构"""

    server: str = Field(
        default="", validate_default=True, description="工具提供者的服务地址"
    )
    description: str = Field(
        default="", validate_default=True, description="工具提供者的描述"
    )
    paths: dict[str, dict] = Field(
        default_factory=dict, validate_default=True, description="工具提供者的路径参数"
    )

    @field_validator("server", mode="before")
    def validate_server(cls, server: str) -> str:
        """校验server字段"""
        if server is None or server == "":
            raise ValidateErrorException("server字段不能为空")
        return server

    @field_validator("description", mode="before")
    def validate_description(cls, description: str) -> str:
        """校验description字段"""
        if description is None or description == "":
            raise ValidateErrorException("description字段不能为空")
        return description

    @field_validator("paths", mode="before")
    def validate_paths(cls, paths: dict[str, dict]) -> dict[str, dict]:
        """校验paths字段"""
        if paths is None or not isinstance(paths, dict):
            raise ValidateErrorException("paths字段不能为空")
        # 提取paths里的每一个元素，并获取元素下的get/post方法对应的值
        methods = ["get", "post"]
        interfaces = []
        extra_paths = {}
        for path, value in paths.items():
            if not isinstance(value, dict):
                raise ValidateErrorException("paths字段的值必须是字典类型")
            for method in methods:
                if method in value:
                    interfaces.append(
                        {"path": path, "method": method, "operation": value[method]}
                    )
        # 遍历提取到的所有接口并校验信息，涵盖operationId唯一标识，parameters参数
        operation_ids = []
        for interface in interfaces:
            # 校验description/operationId/parameters字段
            if not isinstance(interface["operation"].get("description"), str):
                raise ValidateErrorException("description字段不能为空")
            if not isinstance(interface["operation"].get("operationId"), str):
                raise ValidateErrorException("operationId字段不能为空")
            if not isinstance(interface["operation"].get("parameters", []), list):
                raise ValidateErrorException("parameters字段必须是列表类型")

            # 校验operationId字段是否唯一
            if interface["operation"]["operationId"] in operation_ids:
                raise ValidateErrorException(
                    f"operationId字段必须唯一, 重复值为{interface['operation']['operationId']}"
                )
            operation_ids.append(interface["operation"]["operationId"])

            # 校验parameters参数格式是否正确
            for parameter in interface["operation"].get("parameters", []):
                # 校验name/in/description/required/type字段是否存在并且类型正确
                if not isinstance(parameter.get("name"), str):
                    raise ValidateErrorException("name字段不能为空")
                if not isinstance(parameter.get("description"), str):
                    raise ValidateErrorException("description字段不能为空")
                if not isinstance(parameter.get("required"), bool):
                    raise ValidateErrorException("required字段不能为空")
                if (
                    not isinstance(parameter.get("in"), str)
                    or parameter.get("in") not in ParameterIn.__members__.values()
                ):
                    raise ValidateErrorException(
                        f"in字段必须是{ParameterIn.__members__.values()}中的一个"
                    )
                if (
                    not isinstance(parameter.get("type"), str)
                    or parameter.get("type") not in ParameterType.__members__.values()
                ):
                    raise ValidateErrorException(
                        f"type字段必须是{ParameterType.__members__.values()}中的一个"
                    )
            # 组装数据并更新
            extra_paths[interface["path"]] = {
                interface["method"]: {
                    "description": interface["operation"]["description"],
                    "operationId": interface["operation"]["operationId"],
                    "parameters": [
                        {
                            "name": parameter["name"],
                            "in": parameter["in"],
                            "description": parameter["description"],
                            "required": parameter["required"],
                            "type": parameter["type"],
                        }
                        for parameter in interface["operation"].get("parameters", [])
                    ],
                }
            }
        return extra_paths
