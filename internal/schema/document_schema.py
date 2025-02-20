import uuid
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, AnyOf, ValidationError
from .schema import ListField, DictField
from internal.entity.dataset_entity import ProcessType, DEFAULT_PROCESS_RULE
from marshmallow import Schema, fields, pre_dump
from internal.model import Document


class CreateDocumentReq(FlaskForm):
    """创建/新增文档请求"""

    upload_file_ids = ListField("upload_file_ids")
    process_type = StringField(
        "process_type",
        validators=[
            DataRequired("文档处理类型不能为空"),
            AnyOf(
                values=[ProcessType.AUTOMATIC, ProcessType.CUSTOM],
                message="文档处理类型不合法",
            ),
        ],
    )
    rule = DictField("rule")

    def validate_upload_file_ids(self, field: ListField) -> None:
        """校验上传文件id列表"""
        # 校验数据类型与非空
        if not isinstance(field.data, list):
            raise ValidationError("上传文件id列表格式必须是数组")

        # 校验数据长度，最长不超过10条记录
        if len(field.data) > 10 or len(field.data) == 0:
            raise ValidationError("新增文档数量必须在1-10之间")

        # 循环校验id是否为uuid格式
        for upload_file_id in field.data:
            try:
                uuid.UUID(upload_file_id)
            except ValueError:
                raise ValidationError("上传文件id格式必须是uuid格式")

        # 删除重复数据并更新
        field.data = list(dict.fromkeys(field.data))

    def validate_rule(self, field: DictField) -> None:
        """校验处理规则"""
        # 校验处理模式，如果为自动，则为rule赋值默认值
        if self.process_type.data == ProcessType.AUTOMATIC:
            field.data = DEFAULT_PROCESS_RULE["rule"]
        else:
            # 检测自定义规则是否为空
            if not isinstance(field.data, dict) or len(field.data) == 0:
                raise ValidationError("自定义处理规则格式必须是字典")

            # 校验pre_process_rules, 涵盖：非空、列表类型
            if "pre_process_rules" not in field.data or not isinstance(
                field.data["pre_process_rules"], list
            ):
                raise ValidationError(
                    "自定义处理规则中pre_process_rules字段必须是列表类型"
                )

            # 提取pre_process_rules中唯一的处理规则，避免重复处理
            unique_pre_process_rule_dict = {}
            for pre_process_rule in field.data["pre_process_rules"]:
                if "id" not in pre_process_rule or pre_process_rule["id"] not in [
                    "remove_extra_space",
                    "remove_url_and_email",
                ]:
                    raise ValidationError(
                        "自定义处理规则中pre_process_rules字段中id必须是remove_extra_space或remove_url_and_email"
                    )

                # 校验enabled字段，必须是bool类型
                if "enabled" not in pre_process_rule or not isinstance(
                    pre_process_rule["enabled"], bool
                ):
                    raise ValidationError(
                        "自定义处理规则中pre_process_rules字段中enabled必须是bool类型"
                    )

                # 将数据添加到唯一字典中，过滤无关的数据
                unique_pre_process_rule_dict[pre_process_rule["id"]] = {
                    "id": pre_process_rule["id"],
                    "enabled": pre_process_rule["enabled"],
                }

            # 判断一下是否传递了两个处理规则
            if len(unique_pre_process_rule_dict) != 2:
                raise ValidationError("预处理规则格式错误")

            # 将处理后的数据转换成列表并覆盖预处理规则
            field.data["pre_process_rules"] = list(
                unique_pre_process_rule_dict.values()
            )

            # 校验segment字段，涵盖：非空、字典类型
            if "segment" not in field.data or not isinstance(
                field.data["segment"], dict
            ):
                raise ValidationError("自定义处理规则中segment字段必须是字典类型")

            # 校验分隔符separators，涵盖：非空、列表类型、子元素为字符串类型
            if "separators" not in field.data["segment"] or not isinstance(
                field.data["segment"]["separators"], list
            ):
                raise ValidationError(
                    "自定义处理规则中segment字段中separators字段必须是列表类型"
                )

            # 校验分隔符separators，子元素为字符串类型
            for separator in field.data["segment"]["separators"]:
                if not isinstance(separator, str):
                    raise ValidationError(
                        "自定义处理规则中segment字段中separators字段中元素必须是字符串类型"
                    )
            if len(field.data["segment"]["separators"]) == 0:
                raise ValidationError(
                    "自定义处理规则中segment字段中separators字段不能为空"
                )

            # 校验chunk_size字段，涵盖：非空、int类型、范围
            if "chunk_size" not in field.data["segment"] or not isinstance(
                field.data["segment"]["chunk_size"], int
            ):
                raise ValidationError(
                    "自定义处理规则中segment字段中chunk_size字段必须是int类型"
                )
            if (
                field.data["segment"]["chunk_size"] < 100
                or field.data["segment"]["chunk_size"] > 1000
            ):
                raise ValidationError(
                    "自定义处理规则中segment字段中chunk_size字段必须在100-1000之间"
                )

            # 校验块重叠大小chunk_overlap字段，涵盖：非空、int类型、范围
            if "chunk_overlap" not in field.data["segment"] or not isinstance(
                field.data["segment"]["chunk_overlap"], int
            ):
                raise ValidationError(
                    "自定义处理规则中segment字段中块重叠大小chunk_overlap字段必须是int类型"
                )
            if not (
                0
                <= field.data["segment"]["chunk_overlap"]
                <= field.data["segment"]["chunk_size"] * 0.5
            ):
                raise ValidationError(
                    f"自定义处理规则中segment字段中块重叠大小chunk_overlap字段必须在0-{int(field.data['segment']['chunk_size']*0.5)}之间"
                )

            # 更新并剔除多余数据
            field.data = {
                "pre_process_rules": field.data["pre_process_rules"],
                "segment": {
                    "separators": field.data["segment"]["separators"],
                    "chunk_size": field.data["segment"]["chunk_size"],
                    "chunk_overlap": field.data["segment"]["chunk_overlap"],
                },
            }


class CreateDocumentResp(Schema):
    """创建/新增文档响应"""

    documents = fields.List(fields.Dict, dump_default=[])
    batch = fields.String(dump_default="")

    @pre_dump
    def process_data(self, data: tuple[list[Document], str], **kwargs):
        return {
            "documents": [
                {
                    "id": document.id,
                    "name": document.name,
                    "status": document.status,
                    "created_at": int(document.created_at.timestamp()),
                }
                for document in data[0]
            ],
            "batch": data[1],
        }
