from flask_wtf import FlaskForm
from wtforms import StringField, ValidationError
from wtforms.validators import DataRequired, Length, URL
from .schema import ListField


class ValidateOpenAPISchemaReq(FlaskForm):
    """校验OpenAPI规范字符串请求"""

    openapi_schema = StringField(
        "openapi_schema", validators=[DataRequired(message="openapi_schema不能为空")]
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

    headers = ListField("headers")

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
