from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class ValidateOpenAPISchemaReq(FlaskForm):
    """校验OpenAPI规范字符串请求"""

    openapi_schema = StringField(
        "openapi_schema", validators=[DataRequired(message="openapi_schema不能为空")]
    )
