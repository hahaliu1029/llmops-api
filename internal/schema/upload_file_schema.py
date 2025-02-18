from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed, FileSize
from internal.entity.upload_file_entity import (
    ALLOWED_DOCUMENT_EXTENSION,
    ALLOWED_IMAGE_EXTENSION,
)
from marshmallow import Schema, fields, pre_dump
from internal.model import UploadFile


class UploadFileReq(FlaskForm):
    """上传文件请求"""

    file = FileField(
        "file",
        validators=[
            FileRequired("上传文件不能为空"),
            FileSize(max_size=1024 * 1024 * 15, message="文件大小不能超过15M"),
            FileAllowed(
                ALLOWED_DOCUMENT_EXTENSION,
                message=f"文件类型只能是{','.join(ALLOWED_DOCUMENT_EXTENSION)}",
            ),
        ],
    )


class UploadFileResp(Schema):
    """上传文件接口响应结构"""

    id = fields.UUID(default="")
    account_id = fields.UUID(default="")
    name = fields.String(default="")
    key = fields.String(default="")
    size = fields.Integer(default=0)
    extension = fields.String(default="")
    mime_type = fields.String(default="")
    created_at = fields.Integer(default=0)

    @pre_dump
    def pre_dump(self, data: UploadFile, **kwargs):
        return {
            "id": data.id,
            "account_id": data.account_id,
            "name": data.name,
            "key": data.key,
            "size": data.size,
            "extension": data.extension,
            "mime_type": data.mime_type,
            "created_at": int(data.created_at.timestamp()),
        }


class UploadImageReq(FlaskForm):
    """上传图片请求"""

    file = FileField(
        "file",
        validators=[
            FileRequired("上传图片不能为空"),
            FileSize(max_size=1024 * 1024 * 15, message="文件大小不能超过15M"),
            FileAllowed(
                ALLOWED_IMAGE_EXTENSION,
                message=f"文件类型只能是{','.join(ALLOWED_IMAGE_EXTENSION)}",
            ),
        ],
    )
