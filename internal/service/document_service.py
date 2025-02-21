import logging
import random
import time
from typing import List
from injector import inject
from dataclasses import dataclass

from sqlalchemy import UUID, asc, desc, func

from internal.exception import ForbiddenException, FailException, NotFoundException
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
from internal.entity.dataset_entity import ProcessType, SegmentStatus
from internal.model import (
    Document,
    Dataset,
    UploadFile,
    ProcessRule,
    upload_file,
    Segment,
)
from internal.entity.upload_file_entity import ALLOWED_DOCUMENT_EXTENSION
from internal.task.document_task import build_documents
from internal.lib.helper import datetime_to_timestamp


@inject
@dataclass
class DocumentService(BaseService):
    """文档服务"""

    db: SQLAlchemy

    def create_documents(
        self,
        dataset_id: UUID,
        upload_file_ids: List[UUID],
        process_type: str = ProcessType.AUTOMATIC,
        rule: dict = None,
    ) -> tuple[List[Document], str]:
        """根据传递的信息创建文档列表并调用异步任务"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 检测知识库权限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise ForbiddenException("无权限操作该知识库或知识库不存在")

        # 提取文件并校验文件权限与文件扩展
        upload_files = (
            self.db.session.query(UploadFile)
            .filter(
                UploadFile.account_id == account_id,
                UploadFile.id.in_(upload_file_ids),
            )
            .all()
        )

        upload_files = [
            upload_file
            for upload_file in upload_files
            if upload_file.extension.lower() in ALLOWED_DOCUMENT_EXTENSION
        ]

        if len(upload_files) == 0:
            logging.warning(
                f"上传文件中没有合法的文档文件, upload_file_ids: {upload_file_ids}, account_id: {account_id}, dataset_id: {dataset_id}"
            )
            raise FailException("上传文件中没有合法的文档文件")

        # 创建批次与处理规则并记录到数据库
        batch = time.strftime("%Y%m%d%H%M%S" + str(random.randint(100000, 999999)))
        process_rule = self.create(
            ProcessRule,
            account_id=account_id,
            dataset_id=dataset_id,
            mode=process_type,
            rule=rule,
        )

        # 获取当前知识库的最新文档位置
        position = self.get_latest_document_position(dataset_id)

        # 循环遍历所有合法的上传文件列表并记录
        documents = []
        for upload_file in upload_files:
            position += 1
            document = self.create(
                Document,
                account_id=account_id,
                dataset_id=dataset_id,
                upload_file_id=upload_file.id,
                process_rule_id=process_rule.id,
                position=position,
                batch=batch,
                name=upload_file.name,
            )
            documents.append(document)

        # 调用异步任务，完成后续操作
        build_documents.delay([document.id for document in documents])

        # 返回文档列表与处理批次
        return documents, batch

    def get_documents_status(self, dataset_id: UUID, batch: str) -> list[dict]:
        """根据传递的知识库id和批次号获取文档列表状态"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 检测知识库权限
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise ForbiddenException("无权限操作该知识库或知识库不存在")

        # 查询当前知识库下该批次的文档列表
        documents = (
            self.db.session.query(Document)
            .filter(
                Document.dataset_id == dataset_id,
                Document.batch == batch,
            )
            .order_by(asc("position"))
            .all()
        )
        if documents is None or len(documents) == 0:
            raise NotFoundException("该处理批次未找到文档")

        # 循环遍历文档列表提取文档的状态信息
        documents_status = []
        for document in documents:
            # 查询每个文档的总片段书和已构建完成的片段数
            segment_count = (
                self.db.session.query(func.count(Segment.id))
                .filter(Segment.document_id == document.id)
                .scalar()
            )
            completed_segment_count = (
                self.db.session.query(func.count(Segment.id))
                .filter(
                    Segment.document_id == document.id,
                    Segment.status == SegmentStatus.COMPLETED,
                )
                .scalar()
            )

            upload_file = document.upload_file
            documents_status.append(
                {
                    "id": document.id,
                    "name": document.name,
                    "size": upload_file.size,
                    "extension": upload_file.extension,
                    "mime_type": upload_file.mime_type,
                    "position": document.position,
                    "segment_count": segment_count,
                    "completed_segment_count": completed_segment_count,
                    "error": document.error,
                    "status": document.status,
                    "processing_started_at": datetime_to_timestamp(
                        document.processing_started_at
                    ),
                    "parsing_completed_at": datetime_to_timestamp(
                        document.parsing_completed_at
                    ),
                    "splitting_completed_at": datetime_to_timestamp(
                        document.splitting_completed_at
                    ),
                    "indexing_completed_at": datetime_to_timestamp(
                        document.indexing_completed_at
                    ),
                    "completed_at": datetime_to_timestamp(document.completed_at),
                    "stopped_at": datetime_to_timestamp(document.stopped_at),
                    "created_at": datetime_to_timestamp(document.created_at),
                }
            )

        return documents_status

    def get_latest_document_position(self, dataset_id: UUID) -> int:
        """根据传递的知识库id获取最新文档位置"""
        document = (
            self.db.session.query(Document)
            .filter(Document.dataset_id == dataset_id)
            .order_by(desc("position"))
            .first()
        )
        return document.position if document is not None else 0
