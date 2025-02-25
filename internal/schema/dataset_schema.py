from re import search
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField
from wtforms.validators import DataRequired, Length, URL, Optional, AnyOf, NumberRange
from marshmallow import Schema, fields, pre_dump
from internal.model import Dataset, DatasetQuery
from pkg.paginator import PaginatorReq
from internal.entity.dataset_entity import RetrievalSource, RetrievalStrategy
from internal.lib.helper import datetime_to_timestamp


class CreateDatasetReq(FlaskForm):
    """创建知识库请求"""

    name = StringField(
        "name",
        validators=[
            DataRequired("知识库名称不能为空"),
            Length(max=100, message="知识库名称不能超过100个字符"),
        ],
    )
    icon = StringField(
        "icon",
        validators=[
            DataRequired("知识库图标不能为空"),
            URL(message="图标链接格式错误"),
        ],
    )
    description = StringField(
        "description",
        default="",
        validators=[
            Optional(),
            Length(max=2000, message="知识库描述不能超过2000个字符"),
        ],
    )


class GetDatasetResp(Schema):
    """获取知识库详情响应结构"""

    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    document_count = fields.Integer(dump_default=0)
    hit_count = fields.Integer(dump_default=0)
    related_app_count = fields.Integer(dump_default=0)
    character_count = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Dataset, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "document_count": data.document_count,
            "hit_count": data.hit_count,
            "related_app_count": data.related_app_count,
            "character_count": data.character_count,
            "updated_at": int(data.updated_at.timestamp()),
            "created_at": int(data.created_at.timestamp()),
        }


class UpdateDatasetReq(FlaskForm):
    """更新知识库请求"""

    name = StringField(
        "name",
        validators=[
            DataRequired("知识库名称不能为空"),
            Length(max=100, message="知识库名称不能超过100个字符"),
        ],
    )
    icon = StringField(
        "icon",
        validators=[
            DataRequired("知识库图标不能为空"),
            URL(message="图标链接格式错误"),
        ],
    )
    description = StringField(
        "description",
        default="",
        validators=[
            Optional(),
            Length(max=2000, message="知识库描述不能超过2000个字符"),
        ],
    )


class GetDatasetsWithPageReq(PaginatorReq):
    """获取知识库分页列表请求数据"""

    search_word = StringField(
        "search_word",
        default="",
        validators=[Optional()],
    )


class GetDatasetsWithPageResp(Schema):
    """获取知识库分页列表响应数据"""

    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    document_count = fields.Integer(dump_default=0)
    related_app_count = fields.Integer(dump_default=0)
    character_count = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: Dataset, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "document_count": data.document_count,
            "related_app_count": data.related_app_count,
            "character_count": data.character_count,
            "updated_at": int(data.updated_at.timestamp()),
            "created_at": int(data.created_at.timestamp()),
        }


class HitReq(FlaskForm):
    """知识库召回测试请求"""

    query = StringField(
        "query",
        validators=[
            DataRequired("检索参数不能为空"),
            Length(max=200, message="检索参数不能超过200个字符"),
        ],
    )
    retrieval_strategy = StringField(
        "retrieval_strategy",
        validators=[
            DataRequired("检索策略不能为空"),
            AnyOf(
                [strategy.value for strategy in RetrievalStrategy],
                message="检索策略不合法",
            ),
        ],
    )
    k = IntegerField(
        "k",
        validators=[
            DataRequired("最大召回数量不能为空"),
            NumberRange(min=1, max=10, message="最大召回数量范围为1-10"),
        ],
    )
    score = FloatField(
        "score",
        validators=[
            NumberRange(min=0, max=0.99, message="最小匹配度范围为0-0.99"),
        ],
    )


class GetDatasetQueriesResp(Schema):
    """获取知识库检索记录响应结构"""

    id = fields.UUID(dump_default="")
    dataset_id = fields.UUID(dump_default="")
    query = fields.String(dump_default="")
    source = fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: DatasetQuery, **kwargs):
        return {
            "id": data.id,
            "dataset_id": data.dataset_id,
            "query": data.query,
            "source": data.source,
            "created_at": datetime_to_timestamp(data.created_at),
        }
