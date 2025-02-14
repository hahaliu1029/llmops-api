from marshmallow import Schema, fields, pre_dump
from flask_wtf import FlaskForm
from wtforms import StringField, ValidationError
from wtforms.validators import DataRequired, Length, URL, Optional
from .schema import ListField
from internal.model import ApiToolProvider, ApiTool
from pkg.paginator import PaginatorReq


class ValidateOpenAPISchemaReq(FlaskForm):
    """校验OpenAPI规范字符串请求"""

    openapi_schema = StringField(
        "openapi_schema", validators=[DataRequired(message="openapi_schema不能为空")]
    )


class GetApiToolProvidersWithPageReq(PaginatorReq):
    """获取API工具提供者列表信息请求"""

    search_word = StringField(
        "search_word",
        validators=[
            Optional(),
        ],
    )


class CreateApiToolReq(FlaskForm):
    """创建自定义API工具请求"""

    name = StringField(
        "name",
        validators=[
            DataRequired(message="工具提供者名称不能为空"),
            Length(min=1, max=30, message="工具提供者名称长度必须在1-30之间"),
        ],
    )
    icon = StringField(
        "icon",
        validators=[
            DataRequired(message="工具提供者图标不能为空"),
            URL(message="工具提供者图标必须是URL"),
        ],
    )
    openapi_schema = StringField(
        "openapi_schema",
        validators=[
            DataRequired(message="openapi_schema不能为空"),
        ],
    )

    headers = ListField("headers", default=[])

    @classmethod
    def validate_headers(cls, form, field):
        """校验headers字段请求的数据是否正确，涵盖列表校验，列表元素校验"""
        print("field.data", field.data)
        for header in field.data:
            print("header", header)
            if not isinstance(header, dict):
                raise ValidationError("headers字段元素必须是字典类型")
            if "key" not in header or "value" not in header:
                raise ValueError("headers字段元素必须包含key和value字段")
            if not isinstance(header["key"], str) or not isinstance(
                header["value"], str
            ):
                raise ValueError("headers字段元素key和value必须是字符串类型")


class UpdateApiToolProviderReq(FlaskForm):
    """更新API工具提供者请求"""

    name = StringField(
        "name",
        validators=[
            DataRequired(message="工具提供者名称不能为空"),
            Length(min=1, max=30, message="工具提供者名称长度必须在1-30之间"),
        ],
    )
    icon = StringField(
        "icon",
        validators=[
            DataRequired(message="工具提供者图标不能为空"),
            URL(message="工具提供者图标必须是URL"),
        ],
    )
    openapi_schema = StringField(
        "openapi_schema",
        validators=[
            DataRequired(message="openapi_schema不能为空"),
        ],
    )

    headers = ListField("headers", default=[])

    @classmethod
    def validate_headers(cls, form, field):
        """校验headers字段请求的数据是否正确，涵盖列表校验，列表元素校验"""
        print("field.data", field.data)
        for header in field.data:
            print("header", header)
            if not isinstance(header, dict):
                raise ValidationError("headers字段元素必须是字典类型")
            if "key" not in header or "value" not in header:
                raise ValueError("headers字段元素必须包含key和value字段")
            if not isinstance(header["key"], str) or not isinstance(
                header["value"], str
            ):
                raise ValueError("headers字段元素key和value必须是字符串类型")


class GetApiToolProviderResp(Schema):
    """获取API工具提供者响应"""

    id = fields.UUID()
    name = fields.String()
    icon = fields.String()
    openapi_schema = fields.String()
    headers = fields.List(fields.Dict, default=[])
    created_at = fields.Integer(default=0)
    # updated_at = fields.Integer(default=0)

    @pre_dump
    def format_headers(self, data: ApiToolProvider, **kwargs):
        """格式化headers字段"""
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "openapi_schema": data.openapi_schema,
            "headers": data.headers,
            "created_at": int(data.created_at.timestamp()),
        }


class GetApiToolResp(Schema):
    """获取API工具响应"""

    id = fields.UUID()
    name = fields.String()
    description = fields.String()
    inputs = fields.List(fields.Dict, default=[])
    provider = fields.Dict()

    @pre_dump
    def format_provider(self, data: ApiTool, **kwargs):
        """格式化provider字段"""
        provider = data.provider
        return {
            "id": data.id,
            "name": data.name,
            "description": data.description,
            "inputs": [
                {k: v for k, v in parameter.items() if k != "in"}
                for parameter in data.parameters
            ],
            "provider": {
                "id": provider.id,
                "name": provider.name,
                "icon": provider.icon,
                "description": provider.description,
                "headers": provider.headers,
            },
        }


class GetApiToolProvidersWithPageResp(Schema):
    """获取API工具提供者列表信息响应"""

    id = fields.UUID()
    name = fields.String()
    icon = fields.String()
    description = fields.String()
    headers = fields.List(fields.Dict, default=[])
    tools = fields.List(fields.Dict, default=[])
    created_at = fields.Integer(default=0)

    @pre_dump
    def process_data(self, data: ApiToolProvider, **kwargs):
        tools = data.tools
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "headers": data.headers,
            "tools": [
                {
                    "id": tool.id,
                    "name": tool.name,
                    "description": tool.description,
                    "inputs": [
                        {k: v for k, v in parameter.items() if k != "in"}
                        for parameter in tool.parameters
                    ],
                }
                for tool in tools
            ],
            "created_at": int(data.created_at.timestamp()),
        }
