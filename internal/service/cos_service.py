from datetime import datetime
import hashlib
import os
import uuid
from injector import inject
from dataclasses import dataclass
from werkzeug.datastructures import FileStorage

from qcloud_cos import CosConfig, CosS3Client

from internal.model import UploadFile
from internal.entity.upload_file_entity import (
    ALLOWED_DOCUMENT_EXTENSION,
    ALLOWED_IMAGE_EXTENSION,
)
from internal.exception import FailException
from internal.model import Account
from .upload_file_service import UploadFileService


@inject
@dataclass
class CosService:
    """腾讯云COS对象存储服务"""

    upload_file_service: UploadFileService

    @classmethod
    def _get_client(cls) -> CosS3Client:
        """获取COS客户端"""
        conf = CosConfig(
            Region=os.getenv("COS_REGION"),
            SecretId=os.getenv("COS_SECRET_ID"),
            SecretKey=os.getenv("COS_SECRET_KEY"),
            Token=None,
            Scheme=os.getenv("COS_SCHEME", "https"),
        )

        return CosS3Client(conf)

    @classmethod
    def _get_bucket(cls) -> str:
        """获取COS存储桶"""
        return os.getenv("COS_BUCKET")

    def upload_file(
        self, file: FileStorage, account: Account, only_image: bool = False
    ) -> UploadFile:
        """上传文件到COS，上传后返回文件信息"""

        # 提取文件扩展名并检测是否可以上传
        filename = file.filename
        extension = filename.rsplit(".", 1)[-1] if "." in filename else ""

        if extension.lower() not in (
            ALLOWED_IMAGE_EXTENSION + ALLOWED_DOCUMENT_EXTENSION
        ):
            raise FailException(f"该{extension}文件类型不支持上传")
        elif only_image and extension.lower() not in ALLOWED_IMAGE_EXTENSION:
            raise FailException(f"只支持上传图片文件,该{extension}文件类型不支持上传")

        # 获取客户端+存储桶名字
        client = self._get_client()
        bucket = self._get_bucket()

        # 生成一个随机的文件名
        random_filename = str(uuid.uuid4()) + "." + extension
        now = datetime.now()
        upload_filename = f"{now.year}/{now.month:02d}/{now.day:02d}/{random_filename}"

        # 流式读取上传的数据并上传
        file_content = file.stream.read()

        try:
            client.put_object(bucket, file_content, upload_filename)
        except Exception as e:
            raise FailException(f"上传文件失败:{e}")

        # 创建upload_file服务
        return self.upload_file_service.create_upload_file(
            account_id=account.id,
            name=filename,
            key=upload_filename,
            size=len(file_content),
            extension=extension,
            mime_type=file.mimetype,
            hash=hashlib.sha3_256(file_content).hexdigest(),
        )

    def get_file_url(
        self,
        key: str,
    ) -> str:
        """获取文件的URL"""
        # 获取客户端+存储桶名字
        cos_domain = os.getenv("COS_DOMAIN")

        if not cos_domain:
            bucket = os.getenv("COS_BUCKET")
            region = os.getenv("COS_REGION")
            scheme = os.getenv("COS_SCHEME", "https")
            cos_domain = f"{scheme}://{bucket}.cos.{region}.myqcloud.com"

        return f"{cos_domain}/{key}"

    def download_file(self, key: str, target_file_path: str):
        """下载文件到本地"""
        # 获取客户端+存储桶名字
        client = self._get_client()
        bucket = self._get_bucket()

        # 下载文件
        client.download_file(bucket, key, target_file_path)
