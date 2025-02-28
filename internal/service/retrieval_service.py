from uuid import UUID
from injector import inject
from dataclasses import dataclass

from sqlalchemy import update

from internal.model.dataset import Segment
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
from internal.entity.dataset_entity import RetrievalSource, RetrievalStrategy
from langchain_core.documents import Document as LC_Document
from internal.model import Dataset, DatasetQuery
from internal.exception import NotFoundException
from langchain.retrievers import EnsembleRetriever
from .vector_database_service import VectorDatabaseService
from .jieba_service import JiebaService


@inject
@dataclass
class RetrievalService(BaseService):
    """检索服务"""

    db: SQLAlchemy
    vector_database_service: VectorDatabaseService
    jieba_service: JiebaService

    def search_in_datasets(
        self,
        dataset_ids: list[UUID],
        query: str,
        retrieval_strategy: str = RetrievalStrategy.SEMANTIC,
        k: int = 4,
        score: float = 0.0,
        retrieval_source: str = RetrievalSource.HIT_TESTING,
    ) -> list[LC_Document]:
        """根据传递的query+知识库列表进行检索， 并返回检索的文档+得分数据（如果检索策略为全文检索，则得分为0）"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 提取知识库列表并校验权限，同时更新知识库id
        datasets = (
            self.db.session.query(Dataset)
            .filter(Dataset.id.in_(dataset_ids), Dataset.account_id == account_id)
            .all()
        )

        if datasets is None or len(datasets) == 0:
            raise NotFoundException("当前无知识库可执行检索")

        dataset_ids = [dataset.id for dataset in datasets]

        # 构建不同种类的检索器
        from internal.core.retrievers import FullTextRetriever, SemanticRetriever

        semantic_retriever = SemanticRetriever(
            dataset_ids=dataset_ids,
            vector_store=self.vector_database_service.vector_store,
            search_kwargs={"k": k, "score_threshold": score},
        )

        full_text_retriever = FullTextRetriever(
            db=self.db,
            dataset_ids=dataset_ids,
            jieba_service=self.jieba_service,
            search_kwargs={"k": k},
        )

        hybrid_retriever = EnsembleRetriever(
            retrievers=[semantic_retriever, full_text_retriever],
            weights=[0.5, 0.5],
        )

        # 根据检索策略选择检索器
        if retrieval_strategy == RetrievalStrategy.SEMANTIC:
            lc_documents = semantic_retriever.invoke(query)[:k]
        elif retrieval_strategy == RetrievalStrategy.FULL_TEXT:
            lc_documents = full_text_retriever.invoke(query)[:k]
        else:
            lc_documents = hybrid_retriever.invoke(query)[:k]

        # 添加知识库查询记录
        for lc_document in lc_documents:
            self.create(
                DatasetQuery,
                dataset_id=lc_document.metadata["dataset_id"],
                query=query,
                source=retrieval_source,
                # todo:等待APP配置模块完成后进行开发
                source_app_id=None,
                created_by=account_id,
            )

        # 批量更新文档的命中次数，涵盖了构建+执行语句
        with self.db.auto_commit():
            for lc_document in lc_documents:
                stmt = (
                    update(Segment)
                    .where(
                        Segment.id.in_(
                            [
                                lc_document.metadata["segment_id"]
                                for lc_document in lc_documents
                            ]
                        )
                    )
                    .values(hit_count=Segment.hit_count + 1)
                )
                self.db.session.execute(stmt)

        return lc_documents
