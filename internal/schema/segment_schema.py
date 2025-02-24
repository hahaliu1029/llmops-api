from pkg.paginator import PaginatorReq
from wtforms import BooleanField, StringField
from wtforms.validators import Optional, ValidationError, DataRequired
from marshmallow import Schema, fields, pre_dump
from internal.model import Segment
from internal.lib.helper import datetime_to_timestamp
from flask_wtf import FlaskForm
from .schema import ListField


class GetSegmentsWithPageReq(PaginatorReq):
    """获取文档片段列表请求"""

    search_word = StringField(
        "search_word",
        default="",
        validators=[Optional()],
    )


class GetSegmentsWithPageResp(Schema):
    """获取文档片段列表响应"""

    id = fields.UUID(dump_default="")
    document_id = fields.UUID(dump_default="")
    dataset_id = fields.UUID(dump_default="")
    position = fields.Integer(dump_default=0)
    content = fields.String(dump_default="")
    keywords = fields.List(fields.String, dump_default=[])
    character_count = fields.Integer(dump_default=0)
    token_count = fields.Integer(dump_default=0)
    hit_count = fields.Integer(dump_default=0)
    enabled = fields.Boolean(dump_default=False)
    disabled_at = fields.Integer(dump_default=0)
    status = fields.String(dump_default="")
    error = fields.String(dump_default="")
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def pre_dump(self, data: Segment, **kwargs):
        return {
            "id": data.id,
            "document_id": data.document_id,
            "dataset_id": data.dataset_id,
            "position": data.position,
            "content": data.content,
            "keywords": data.keywords,
            "character_count": data.character_count,
            "token_count": data.token_count,
            "hit_count": data.hit_count,
            "enabled": data.enabled,
            "disabled_at": datetime_to_timestamp(data.disabled_at),
            "status": data.status,
            "error": data.error,
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }


class GetSegmentResp(Schema):
    """获取文档片段请求"""

    id = fields.UUID(dump_default="")
    document_id = fields.UUID(dump_default="")
    dataset_id = fields.UUID(dump_default="")
    position = fields.Integer(dump_default=0)
    content = fields.String(dump_default="")
    keywords = fields.List(fields.String, dump_default=[])
    character_count = fields.Integer(dump_default=0)
    token_count = fields.Integer(dump_default=0)
    hit_count = fields.Integer(dump_default=0)
    hash = fields.String(dump_default="")
    enabled = fields.Boolean(dump_default=False)
    disabled_at = fields.Integer(dump_default=0)
    status = fields.String(dump_default="")
    error = fields.String(dump_default="")
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def pre_dump(self, data: Segment, **kwargs):
        return {
            "id": data.id,
            "document_id": data.document_id,
            "dataset_id": data.dataset_id,
            "position": data.position,
            "content": data.content,
            "keywords": data.keywords,
            "character_count": data.character_count,
            "token_count": data.token_count,
            "hit_count": data.hit_count,
            "hash": data.hash,
            "enabled": data.enabled,
            "disabled_at": datetime_to_timestamp(data.disabled_at),
            "status": data.status,
            "error": data.error,
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
        }


class UpdateSegmentEnabledReq(FlaskForm):
    """更新文档片段启用状态请求"""

    enabled = BooleanField("enabled")

    def validate_enabled(self, field: BooleanField) -> None:
        """校验启用状态"""
        if not isinstance(field.data, bool):
            raise ValidationError("文档启用状态必须是bool类型")


class CreateSegmentReq(FlaskForm):
    """创建文档片段请求"""

    content = StringField("content", validators=[DataRequired("文档片段内容不能为空")])
    keywords = ListField(
        "keywords",
    )

    def validate_keywords(self, field: ListField) -> None:
        """校验关键词列表"""
        if field.data is None:
            field.data = []
        if not isinstance(field.data, list):
            raise ValidationError("关键词列表必须是list类型")

        # 校验数据的长度，最长不能超过10个关键词
        if len(field.data) > 10:
            raise ValidationError("关键词列表最多不能超过10个")

        # 循环校验关键词信息，关键词必须是字符串
        for keyword in field.data:
            if not isinstance(keyword, str):
                raise ValidationError("关键词必须是字符串类型")

        # 删除重复数据并更新
        field.data = list(dict.fromkeys(field.data))
