from datetime import datetime
import logging
from uuid import UUID
import re
import uuid
from flask import Flask, current_app
from injector import inject
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import func
from internal.model import Document, Segment, KeywordTable, DatasetQuery
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
from internal.entity.dataset_entity import DocumentStatus, SegmentStatus
from internal.entity.cache_entity import (
    LOCK_DOCUMENT_UPDATE_ENABLED,
    LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE,
    LOCK_EXPIRE_TIME,
)
from langchain_core.documents import Document as LC_Document
from internal.core.file_extractor import FileExtractor
from .process_rule_service import ProcessRuleService
from .embeddings_service import EmbeddingsService
from internal.lib.helper import generate_text_hash
from .jieba_service import JiebaService
from .keyword_table_service import KeywordTableService
from .vector_database_service import VectorDatabaseService
from internal.exception import NotFoundException
from redis import Redis
from weaviate.classes.query import Filter


@inject
@dataclass
class IndexingService(BaseService):
    """索引服务"""

    db: SQLAlchemy
    redis_client: Redis
    file_extractor: FileExtractor
    process_rule_service: ProcessRuleService
    embeddings_service: EmbeddingsService
    jieba_service: JiebaService
    keyword_table_service: KeywordTableService
    vector_database_service: VectorDatabaseService

    def build_documents(self, document_ids: list[UUID]) -> None:
        """根据传递的文档id列表构建知识库文档，涵盖了加载、分割、索引构建、数据存储等内容"""
        # 根据文档id获取所有文档
        documents = (
            self.db.session.query(Document).filter(Document.id.in_(document_ids)).all()
        )

        # 执行循环遍历所有文档完成对每个文档的构建
        for document in documents:
            try:
                # 更新当前状态为解析中，并记录开始处理的时间
                self.update(
                    document,
                    status=DocumentStatus.PARSING,
                    processing_started_at=datetime.now(),
                )

                # 执行文档加载步骤，并更新文档的状态和时间
                lc_documents = self._parsing(document)
                # 执行文档分割步骤，并更新文档的状态和时间，涵盖了片段的信息
                lc_segments = self._splitting(document, lc_documents)

                # 执行文档索引步骤，涵盖关键词提取、向量，并跟新数据状态
                self._indexing(document, lc_segments)
                # 执行文档存储步骤，涵盖文档状态更新，以及向量数据库的存储
                self._completed(document, lc_segments)

            except Exception as e:
                logging.exception(f"构建文档失败, 错误信息: {str(e)}")
                self.update(
                    document,
                    status=DocumentStatus.ERROR,
                    error=str(e),
                    stopped_at=datetime.now(),
                )

    def update_document_enabled(self, document_id: UUID) -> None:
        """根据传递的文档id更新文档的启用状态, 同时修改weaviate向量数据库中的记录"""
        # 构建缓存键
        cache_key = LOCK_DOCUMENT_UPDATE_ENABLED.format(document_id=document_id)

        # 根据传递的文档id获取文档信息
        document = self.get(Document, document_id)
        if document is None:
            logging.exception(f"文档不存在, 文档ID: {document_id}")
            raise NotFoundException("文档不存在")

        # 查找归属于当前文档的所有片段的节点id
        segments = (
            self.db.session.query(Segment)
            .with_entities(Segment.id, Segment.node_id, Segment.enabled)
            .filter(
                Segment.document_id == document_id,
                Segment.status == SegmentStatus.COMPLETED,
            )
            .all()
        )
        segment_ids = [id for id, _, _ in segments]
        node_ids = [node_id for _, node_id, _ in segments]

        # 执行循环遍历所有node_ids并更新向量数据库中的记录
        try:
            collection = self.vector_database_service.collection
            for node_id in node_ids:
                try:
                    collection.data.update(
                        uuid=node_id,
                        properties={"document_enabled": document.enabled},
                    )
                except Exception as e:
                    with self.db.auto_commit():
                        self.db.session.query(Segment).filter(
                            Segment.node_id == node_id
                        ).update(
                            {
                                "error": str(e),
                                "status": SegmentStatus.ERROR,
                                "enabled": False,
                                "disabled_at": datetime.now(),
                                "stopped_at": datetime.now(),
                            }
                        )

            # 更新关键词表对应的数据（enabled为false表示从关键词表中删除数据，enabled为true表示在关键词表中新增数据)
            if document.enabled is True:
                # 从禁用改为启用，需要新增关键词
                enabled_segment_ids = [
                    segment_id for segment_id, _, enabled in segments if enabled is True
                ]
                self.keyword_table_service.add_keyword_table_from_ids(
                    document.dataset_id, enabled_segment_ids
                )
            else:
                # 从启用改为禁用，需要剔除关键词
                self.keyword_table_service.delete_keyword_table_from_ids(
                    document.dataset_id, segment_ids
                )

        except Exception as e:
            # 记录日志并将状态修改回原状态
            logging.exception(
                f"更新向量数据库失败, 文档id: {document_id}, 错误信息: {str(e)}"
            )
            origin_enable = not document.enabled
            self.update(
                document,
                enabled=origin_enable,
                disable_at=None if origin_enable else datetime.now(),
            )
        finally:
            #  删除缓存
            self.redis_client.delete(cache_key)

    def delete_document(self, dataset_id: UUID, document_id: UUID) -> None:
        """根据传递的知识库ID和文档ID删除文档"""
        # 查找该文档下的所有片段id列表
        segment_ids = [
            str(id)
            for id, in self.db.session.query(Segment)
            .with_entities(Segment.id)
            .filter(Segment.document_id == document_id)
            .all()
        ]

        # 调用向量数据库删除其关联记录
        collection = self.vector_database_service.collection
        collection.data.delete_many(
            where=Filter.by_property("document_id").equal(document_id)
        )

        # 删除pgsql关联的片段记录
        with self.db.auto_commit():
            self.db.session.query(Segment).filter(
                Segment.document_id == document_id
            ).delete()

        # 删除片段id对应的关键词记录
        self.keyword_table_service.delete_keyword_table_from_ids(
            dataset_id=dataset_id, segment_ids=segment_ids
        )

    def delete_dataset(self, dataset_id: UUID) -> None:
        """根据传递的知识库ID执行相应删除操作"""
        try:
            with self.db.auto_commit():
                # 删除关联的文档记录
                self.db.session.query(Document).filter(
                    Document.dataset_id == dataset_id
                ).delete()

                # 删除关联的片段记录
                self.db.session.query(Segment).filter(
                    Segment.dataset_id == dataset_id
                ).delete()

                # 删除关联的关键词表记录
                self.db.session.query(KeywordTable).filter(
                    KeywordTable.dataset_id == dataset_id
                ).delete()

                # 删除知识库查询记录
                self.db.session.query(DatasetQuery).filter(
                    DatasetQuery.dataset_id == dataset_id
                ).delete()

                # 调用向量数据库删除知识库的关联记录
                self.vector_database_service.collection.data.delete_many(
                    where=Filter.by_property("dataset_id").equal(str(dataset_id))
                )

        except Exception as e:
            logging.error(
                f"异步删除知识库失败, dataset_id: {dataset_id}, error: {str(e)}"
            )

    def _parsing(self, document: Document) -> list[LC_Document]:
        """解析传递的文档为langchain的文档列表"""
        # 获取upload_file并加载Langchain文档
        upload_file = document.upload_file
        lc_documents = self.file_extractor.load(upload_file, False, True)

        # 循环处理LangChain文档,并删除多余的空白字符串
        for lc_document in lc_documents:
            lc_document.page_content = self._clean_extra_text(lc_document.page_content)

        # 更新文档状态并记录时间
        self.update(
            document,
            character_count=sum(
                [len(lc_document.page_content) for lc_document in lc_documents]
            ),
            status=DocumentStatus.SPLITTING,
            parsing_completed_at=datetime.now(),
        )

        return lc_documents

    def _splitting(
        self, document: Document, lc_documents: list[LC_Document]
    ) -> list[LC_Document]:
        """根据传递的信息进行文档分割，拆分成小块片段"""
        # 根据process_rule获取文本分割器
        process_rule = document.process_rule
        text_splitter = self.process_rule_service.get_text_splitter_by_process_rule(
            process_rule,
            self.embeddings_service.calculate_token_count,
        )

        # 按照process_rule的规则清除多余字符串
        for lc_document in lc_documents:
            lc_document.page_content = (
                self.process_rule_service.clean_text_by_process_rule(
                    lc_document.page_content, process_rule
                )
            )

        # 分割文档列表为片段列表
        lc_segments = text_splitter.split_documents(lc_documents)

        # 获取对应文档下的最大片段位置
        position = (
            self.db.session.query(func.coalesce(func.max(Segment.position), 0))
            .filter(Segment.document_id == document.id)
            .scalar()
        )

        # 循环处理片段数据并添加元数据，同时存储到pgsql数据库
        segments = []
        for lc_segment in lc_segments:
            position += 1
            content = lc_segment.page_content
            segment = self.create(
                Segment,
                account_id=document.account_id,
                dataset_id=document.dataset_id,
                document_id=document.id,
                node_id=uuid.uuid4(),
                position=position,
                content=content,
                character_count=len(content),
                token_count=self.embeddings_service.calculate_token_count(content),
                hash=generate_text_hash(content),
                status=SegmentStatus.WAITING,
            )
            lc_segment.metadata = {
                "account_id": str(document.account_id),
                "dataset_id": str(document.dataset_id),
                "document_id": str(document.id),
                "segment_id": str(segment.id),
                "node_id": str(segment.node_id),
                "document_enabled": False,
                "segment_enabled": False,
            }
            segments.append(segment)

        # 更新文档的数据，涵盖状态、token数等内容
        self.update(
            document,
            token_count=sum([segment.token_count for segment in segments]),
            status=DocumentStatus.INDEXING,
            splitting_completed_at=datetime.now(),
        )

        return lc_segments

    def _indexing(self, document: Document, lc_segments: list[LC_Document]) -> None:
        """根据传递的信息构建索引，涵盖关键词提取、词表构建"""
        for lc_segment in lc_segments:
            # 提取每一个片段对应的关键词，关键词的数量最多不超过10个
            keywords = self.jieba_service.extract_keywords(lc_segment.page_content, 10)

            # 逐条更新文档片段的关键词
            self.db.session.query(Segment).filter(
                Segment.id == lc_segment.metadata["segment_id"]
            ).update(
                {
                    "keywords": keywords,
                    "status": SegmentStatus.INDEXING,
                    "indexing_completed_at": datetime.now(),
                }
            )

            # 获取当前知识库的关键词表
            keyword_table_record = (
                self.keyword_table_service.get_keyword_table_from_dataset_id(
                    document.dataset_id
                )
            )
            keyword_table = {
                field: set(value)
                for field, value in keyword_table_record.keyword_table.items()
            }

            # 循环处理关键词并更新关键词表
            for keyword in keywords:
                if keyword not in keyword_table:
                    keyword_table[keyword] = set()
                keyword_table[keyword].add(lc_segment.metadata["segment_id"])

            # 更新关键词表
            self.update(
                keyword_table_record,
                keyword_table={
                    field: list(value) for field, value in keyword_table.items()
                },
            )
        # 更新文档状态
        self.update(
            document,
            indexing_completed_at=datetime.now(),
        )

    def _completed(self, document: Document, lc_segments: list[LC_Document]) -> None:
        """根据传递的信息完成文档的构建，涵盖文档状态更新、向量数据库存储"""
        # 循环遍历片段列表数据，将文档状态以及片段状态设置为True
        for lc_segment in lc_segments:
            lc_segment.metadata["document_enabled"] = True
            lc_segment.metadata["segment_enabled"] = True

        def thread_func(
            flask_app: Flask, chunks: list[LC_Document], ids: list[UUID]
        ) -> None:
            """线程函数，执行向量数据库与pgsql数据的存储"""
            try:
                with flask_app.app_context():
                    # 调用向量数据库存储对应数据
                    self.vector_database_service.vector_store.add_documents(
                        chunks,
                        ids=ids,
                    )

                    with self.db.auto_commit():
                        # 更新关联片段的状态和完成时间
                        self.db.session.query(Segment).filter(
                            Segment.node_id.in_(ids)
                        ).update(
                            {
                                "status": SegmentStatus.COMPLETED,
                                "completed_at": datetime.now(),
                                "enabled": True,
                            },
                            # synchronize_session=False,
                        )
            except Exception as e:
                logging.exception(f"存储数据失败, 错误信息: {str(e)}")
                with self.db.auto_commit():
                    # 更新关联片段的状态和完成时间
                    self.db.session.query(Segment).filter(
                        Segment.node_id.in_(ids)
                    ).update(
                        {
                            "status": SegmentStatus.ERROR,
                            "completed_at": None,
                            "stopped_at": datetime.now(),
                            "enabled": False,
                        },
                    )

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            # 调用向量数据库，每次存储10条数据，避免一次传递过多数据
            for i in range(0, len(lc_segments), 10):
                # 提取需要存储的数据和ids
                chunks = lc_segments[i : i + 10]
                # for chunk in chunks:
                #     print(chunk)
                #     print(f"Chunk metadata: {chunk.metadata}")
                ids = [chunk.metadata["node_id"] for chunk in chunks]
                futures.append(
                    executor.submit(
                        thread_func, current_app._get_current_object(), chunks, ids
                    )
                )

            for future in futures:
                future.result()

        # 更新文档状态
        self.update(
            document,
            status=DocumentStatus.COMPLETED,
            completed_at=datetime.now(),
            enabled=True,
        )

    @classmethod
    def _clean_extra_text(cls, text: str) -> str:
        """清除过滤传递的多余空白字符串"""
        text = re.sub(r"<\|", "<", text)
        text = re.sub(r"\|>", ">", text)
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\xEF\xBF\xBE]", "", text)
        text = re.sub("\uFFFE", "", text)  # 删除零宽非标记字符
        return text
