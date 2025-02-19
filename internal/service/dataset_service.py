from uuid import UUID
from injector import inject
from dataclasses import dataclass
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
from internal.schema.dataset_schema import (
    CreateDatasetReq,
    UpdateDatasetReq,
    GetDatasetsWithPageReq,
)
from internal.model import Dataset
from internal.exception import ValidateErrorException, NotFoundException
from internal.entity.dataset_entity import DEFAULT_DATASET_DESCRIPTION_FORMATTER
from pkg.paginator import Paginator
from sqlalchemy import desc


@inject
@dataclass
class DatasetService(BaseService):
    """知识库服务"""

    db: SQLAlchemy

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

    def delete_dataset(self):
        """删除知识库"""
        pass

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
