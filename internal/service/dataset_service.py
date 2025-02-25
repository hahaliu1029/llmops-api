import logging
from uuid import UUID
from injector import inject
from dataclasses import dataclass
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
from internal.schema.dataset_schema import (
    CreateDatasetReq,
    UpdateDatasetReq,
    GetDatasetsWithPageReq,
    HitReq,
)
from internal.model import Dataset, Segment, DatasetQuery, AppDatasetJoin
from internal.exception import ValidateErrorException, NotFoundException, FailException
from internal.entity.dataset_entity import DEFAULT_DATASET_DESCRIPTION_FORMATTER
from pkg.paginator import Paginator
from sqlalchemy import desc
from .retrieval_service import RetrievalService
from internal.lib.helper import datetime_to_timestamp
from internal.task.dataset_task import delete_dataset


@inject
@dataclass
class DatasetService(BaseService):
    """知识库服务"""

    db: SQLAlchemy
    retrieval_service: RetrievalService

    def create_dataset(self, req: CreateDatasetReq) -> Dataset:
        """创建知识库"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 检测该账号下知识库名称是否重复
        dataset = (
            self.db.session.query(Dataset)
            .filter_by(name=req.name.data, account_id=account_id)
            .one_or_none()
        )
        if dataset:
            raise ValidateErrorException(f"该知识库名称{req.name.data}已存在")

        # 检测是否传递了描述信息，如果没有传递需要补充上
        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(
                name=req.name.data
            )

        # 创建知识库并返回
        return self.create(
            Dataset,
            account_id=account_id,
            name=req.name.data,
            icon=req.icon.data,
            description=req.description.data,
        )

    def get_dataset_queries(self, dataset_id: UUID) -> list[DatasetQuery]:
        """根据知识库id获取最近10条检索记录"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 检测知识库是否存在
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise NotFoundException("知识库不存在")

        # 获取最近10条检索记录
        dataset_queries = (
            self.db.session.query(DatasetQuery)
            .filter(DatasetQuery.dataset_id == dataset_id)
            .order_by(desc("created_at"))
            .limit(10)
            .all()
        )

        return dataset_queries

    def update_dataset(self, dataset_id: UUID, req: UpdateDatasetReq) -> Dataset:
        """根据传递的知识库id+信息更新知识库"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 检测知识库是否存在
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise NotFoundException("知识库不存在")

        # 检测修改后的知识库名称是否重复
        dataset_with_same_name = (
            self.db.session.query(Dataset)
            .filter(
                Dataset.name == req.name.data,
                Dataset.account_id == account_id,
                Dataset.id != dataset_id,
            )
            .one_or_none()
        )
        if dataset_with_same_name:
            raise ValidateErrorException(f"该知识库名称{req.name.data}已存在")

        # 校验描述信息是否为空，如果为空，则人为设置
        if req.description.data is None or req.description.data.strip() == "":
            req.description.data = DEFAULT_DATASET_DESCRIPTION_FORMATTER.format(
                name=req.name.data
            )

        # 更新知识库信息
        self.update(
            dataset,
            name=req.name.data,
            icon=req.icon.data,
            description=req.description.data,
        )

        return dataset

    def get_dataset(self, dataset_id: UUID) -> Dataset:
        """根据知识库id获取知识库"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise NotFoundException("知识库不存在")

        return dataset

    def get_datasets_with_page(
        self, req: GetDatasetsWithPageReq
    ) -> tuple[list[Dataset], Paginator]:
        """获取知识库分页+搜索列表数据"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 构建查询条件
        paginator = Paginator(db=self.db, req=req)

        # 构建筛选器
        filters = [Dataset.account_id == account_id]

        if req.search_word.data:
            filters.append(Dataset.name.ilike(f"%{req.search_word.data}%"))

        # 执行分页并获取数据
        datasets = paginator.paginate(
            self.db.session.query(Dataset).filter(*filters).order_by(desc("created_at"))
        )

        return datasets, paginator

    def hit(self, dataset_id: UUID, req: HitReq) -> list[dict]:
        """根据传递的知识库id+请求进行召回测试"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 检测知识库是否存在并校验
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise NotFoundException("知识库不存在")

        # 调用检索服务进行检索
        lc_documents = self.retrieval_service.search_in_datasets(
            dataset_ids=[dataset_id], **req.data
        )

        lc_documents_dict = {
            str(lc_document.metadata["segment_id"]): lc_document
            for lc_document in lc_documents
        }

        # 根据检索到的数据查询对应的片段信息
        segments = (
            self.db.session.query(Segment)
            .filter(
                Segment.id.in_(
                    [
                        str(lc_document.metadata["segment_id"])
                        for lc_document in lc_documents
                    ]
                )
            )
            .all()
        )
        segment_dict = {str(segment.id): segment for segment in segments}

        # 排序片段数据
        sorted_segments = [
            segment_dict[str(lc_document.metadata["segment_id"])]
            for lc_document in lc_documents
            if str(lc_document.metadata["segment_id"]) in segment_dict
        ]

        # 组装响应数据
        hit_result = []

        for segment in sorted_segments:
            document = segment.document
            upload_file = document.upload_file
            hit_result.append(
                {
                    "id": segment.id,
                    "document": {
                        "id": document.id,
                        "name": document.name,
                        "extension": upload_file.extension,
                        "mime_type": upload_file.mime_type,
                    },
                    "dataset_id": segment.dataset_id,
                    "score": lc_documents_dict[str(segment.id)].metadata["score"],
                    "position": segment.position,
                    "content": segment.content,
                    "keywords": segment.keywords,
                    "character_count": segment.character_count,
                    "token_count": segment.token_count,
                    "hit_count": segment.hit_count,
                    "enabled": segment.enabled,
                    "disabled_at": datetime_to_timestamp(segment.disabled_at),
                    "status": segment.status,
                    "error": segment.error,
                    "created_at": datetime_to_timestamp(segment.created_at),
                    "updated_at": datetime_to_timestamp(segment.updated_at),
                }
            )

        return hit_result

    def delete_dataset(self, dataset_id: UUID) -> Dataset:
        """删除知识库,涵盖知识库底下的所有文档、关键词、片段，和向量数据库中存储的数据"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 检测知识库是否存在并校验
        dataset = self.get(Dataset, dataset_id)
        if dataset is None or str(dataset.account_id) != account_id:
            raise NotFoundException("知识库不存在")

        try:
            # 删除知识库基础记录以及知识库和应用关联的记录
            self.delete(dataset)
            with self.db.auto_commit():
                self.db.session.query(AppDatasetJoin).filter(
                    AppDatasetJoin.dataset_id == dataset_id
                ).delete()

            # 调用异步任务执行后续操作
            delete_dataset.delay(dataset_id)
        except Exception as e:
            logging.error(f"删除知识库失败, dataset_id: {dataset_id}, error: {str(e)}")
            raise FailException("删除知识库失败")
