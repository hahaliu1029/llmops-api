from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class CompletionReq(FlaskForm):
    """聊天请求接口验证"""

    # 必填，最大长度2000
    query = StringField(
        "query",
        validators=[
            DataRequired(message="query不能为空"),
            Length(max=2000, message="query长度不能超过2000"),
        ],
    )
