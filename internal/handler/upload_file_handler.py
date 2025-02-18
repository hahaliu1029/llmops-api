from injector import inject
from dataclasses import dataclass
from internal.schema.upload_file_schema import (
    UploadFileReq,
    UploadFileResp,
    UploadImageReq,
)
from pkg.response import validate_error_json, success_json
from internal.service import UploadFileService, CosService


@inject
@dataclass
class UploadFileHandler:
    """上传文件控制器"""

    cos_service: CosService
    upload_file_service: UploadFileService

    def upload_file(self):
        """上传文件/文档"""
        # 构建请求并校验
        req = UploadFileReq()
        if not req.validate():
            return validate_error_json(req.errors)
        # 调用服务上传文件并获取记录
        upload_file = self.cos_service.upload_file(req.file.data)
        # 构建响应并返回
        res = UploadFileResp()
        return success_json(res.dump(upload_file))

    def upload_image(self):
        """上传图片"""
        # 构建请求并校验
        req = UploadImageReq()

        if not req.validate():
            return validate_error_json(req.errors)
        # 调用服务上传图片并获取记录
        upload_file = self.cos_service.upload_file(req.file.data, only_image=True)

        # 获取图片的实际url地址
        image_url = self.cos_service.get_file_url(upload_file.key)

        # 构建响应并返回
        return success_json(
            {
                "image_url": image_url,
            }
        )
