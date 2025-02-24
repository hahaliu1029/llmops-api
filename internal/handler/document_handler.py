from uuid import UUID
from injector import inject
from dataclasses import dataclass
from flask import request
from internal.schema.document_schema import (
    CreateDocumentReq,
    CreateDocumentResp,
    GetDocumentResp,
    UpdateDocumentNameReq,
    GetDocumentsWithPageReq,
    GetDocumentsWithPageResp,
    UpdateDocumentEnabledReq,
)
from pkg.response import validate_error_json, success_json, success_message
from internal.service import DocumentService
from pkg.paginator import PageModel


@inject
@dataclass
class DocumentHandler:
    """文档处理器"""

    document_service: DocumentService

    def create_documents(self, dataset_id: UUID):
        """知识库新增/上传文档列表"""
        # 提取请求并校验
        req = CreateDocumentReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务并创建文档，返回文档列表信息+处理批次
        documents, batch = self.document_service.create_documents(
            dataset_id, **req.data
        )
        # 生成响应结构并返回
        resp = CreateDocumentResp()
        return success_json(resp.dump((documents, batch)))

    def get_document(self, dataset_id: UUID, document_id: UUID):
        """根据传递的知识库ID和文档ID获取文档信息"""
        document = self.document_service.get_document(dataset_id, document_id)
        # 生成响应结构并返回
        resp = GetDocumentResp()
        return success_json(resp.dump(document))

    def update_document_name(self, dataset_id: UUID, document_id: UUID):
        """根据传递的知识库ID和文档ID更新文档名称"""
        # 提取请求并校验
        req = UpdateDocumentNameReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务并更新文档名称
        self.document_service.update_document(
            dataset_id, document_id, name=req.name.data
        )

        return success_message("文档名称更新成功")

    def get_documents_with_page(self, dataset_id: UUID):
        """根据传递的知识库ID获取分页文档列表"""
        # 提取请求并校验
        req = GetDocumentsWithPageReq(request.args)
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务并获取分页文档列表
        documents, paginator = self.document_service.get_documents_with_page(
            dataset_id, req
        )

        # 生成响应结构并返回
        resp = GetDocumentsWithPageResp(many=True)
        return success_json(
            PageModel(
                list=resp.dump(documents),
                paginator=paginator,
            )
        )

    def update_document_enabled(self, dataset_id: UUID, document_id: UUID):
        """根据传递的知识库ID和文档ID更新文档启用状态"""
        # 提取请求并校验
        req = UpdateDocumentEnabledReq()
        if not req.validate():
            return validate_error_json(req.errors)

        # 调用服务并更新文档启用状态
        self.document_service.update_document_enabled(
            dataset_id, document_id, enabled=req.enabled.data
        )

        return success_message("文档启用状态更新成功")

    def get_documents_status(self, dataset_id: UUID, batch: str):
        """根据传递的知识库ID和批次号获取文档处理状态"""
        documents_status = self.document_service.get_documents_status(dataset_id, batch)

        return success_json(documents_status)
