from datetime import datetime
import logging
from uuid import UUID
import uuid
from injector import inject
from dataclasses import dataclass

from sqlalchemy import asc, func
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
from internal.schema.segment_schema import (
    GetSegmentsWithPageReq,
    CreateSegmentReq,
    UpdateSegmentReq,
)
from internal.model import Segment, Document, Account
from pkg.paginator import Paginator
from internal.exception import NotFoundException, FailException, ValidateErrorException
from internal.entity.dataset_entity import SegmentStatus, DocumentStatus
from internal.entity.cache_entity import LOCK_SEGMENT_UPDATE_ENABLED, LOCK_EXPIRE_TIME
from redis import Redis
from .keyword_table_service import KeywordTableService
from .vector_database_service import VectorDatabaseService
from .embeddings_service import EmbeddingsService
from .jieba_service import JiebaService
from internal.lib.helper import generate_text_hash
from langchain_core.documents import Document as LC_Document


@inject
@dataclass
class SegmentService(BaseService):
    """片段服务"""

    db: SQLAlchemy
    redis_client: Redis
    keyword_table_service: KeywordTableService
    vector_database_service: VectorDatabaseService
    embeddings_service: EmbeddingsService
    jieba_service: JiebaService

    def create_segment(
        self,
        dataset_id: UUID,
        document_id: UUID,
        req: CreateSegmentReq,
        account: Account,
    ) -> Segment:
        """根据传递的信息创建片段"""

        # 校验上传内容的token数，不能超过1000
        token_count = self.embeddings_service.calculate_token_count(req.content.data)
        if token_count > 1000:
            raise ValidateErrorException("上传内容的token数不能超过1000")

        # 获取文档信息并校验
        document = self.get(Document, document_id)
        if (
            document is None
            or document.dataset_id != dataset_id
            or document.account_id != account.id
        ):
            raise NotFoundException("文档不存在")

        # 判断文档状态是否可以新增片段，只有completed状态的文档才可以新增片段
        if document.status != DocumentStatus.COMPLETED:
            raise FailException("文档状态异常，无法新增片段")

        # 提取文档片段的最大位置
        position = (
            self.db.session.query(func.coalesce(func.max(Segment.position), 0))
            .filter(Segment.document_id == document_id)
            .scalar()
        )

        # 检测是否传递了keywords，如果没有，调用jieba进行分词
        if req.keywords.data is None or len(req.keywords.data) == 0:
            req.keywords.data = self.jieba_service.extract_keywords(
                req.content.data, 10
            )

        # 往pgsql中新增记录
        segment = None
        try:
            # 位置+1并新增记录
            position += 1
            segment = self.create(
                Segment,
                account_id=account.id,
                dataset_id=dataset_id,
                document_id=document_id,
                node_id=uuid.uuid4(),
                position=position,
                content=req.content.data,
                character_count=len(req.content.data),
                token_count=token_count,
                keywords=req.keywords.data,
                hash=generate_text_hash(req.content.data),
                enabled=True,
                processing_started_at=datetime.now(),
                indexing_completed_at=datetime.now(),
                completed_at=datetime.now(),
                status=SegmentStatus.COMPLETED,
            )

            # 往向量数据库中新增数据
            self.vector_database_service.vector_store.add_documents(
                [
                    LC_Document(
                        page_content=req.content.data,
                        metadata={
                            "account_id": str(document.account_id),
                            "dataset_id": str(document.dataset_id),
                            "document_id": str(document.id),
                            "segment_id": str(segment.id),
                            "node_id": str(segment.node_id),
                            "document_enabled": document.enabled,
                            "segment_enabled": True,
                        },
                    )
                ],
                ids=[str(segment.node_id)],
            )

            # 重新计算片段的字符总数以及token总数
            document_character_count, document_token_count = self.db.session.query(
                func.coalesce(func.sum(Segment.character_count), 0),
                func.coalesce(func.sum(Segment.token_count), 0),
            ).first()

            # 更新文档的字符总数以及token总数
            self.update(
                document,
                character_count=document_character_count,
                token_count=document_token_count,
            )

            # 更新关键词表信息
            if document.enabled is True:
                self.keyword_table_service.add_keyword_table_from_ids(
                    dataset_id, [segment.id]
                )
        except Exception as e:
            logging.exception(f"文档片段新增失败，错误信息：{str(e)}")
            if segment:
                self.update(
                    segment,
                    error=str(e),
                    status=SegmentStatus.ERROR,
                    enabled=False,
                    disabled_at=datetime.now(),
                    stopped_at=datetime.now(),
                )
            raise FailException("文档片段新增失败")

    def get_segments_with_page(
        self,
        dataset_id: UUID,
        document_id: UUID,
        req: GetSegmentsWithPageReq,
        account: Account,
    ) -> tuple[list[Segment], Paginator]:
        """根据传递的信息获取片段列表分页数据"""

        # 获取文档并校验权限
        document = self.get(Document, document_id)
        print(document.account_id)
        if (
            document is None
            or document.dataset_id != dataset_id
            or document.account_id != account.id
        ):
            raise NotFoundException("文档不存在")

        # 构建分页查询器
        paginator = Paginator(db=self.db, req=req)

        # 构建筛选器
        filters = [Segment.document_id == document_id]

        if req.search_word.data:
            filters.append(Segment.content.like(f"%{req.search_word.data}%"))

        # 执行分页并获取数据
        segments = paginator.paginate(
            self.db.session.query(Segment).filter(*filters).order_by(asc("position"))
        )

        return segments, paginator

    def get_segment(
        self, dataset_id: UUID, document_id: UUID, segment_id: UUID, account: Account
    ) -> Segment:
        """根据传递的信息获取片段信息"""

        # 获取片段信息并校验权限
        segment = self.get(Segment, segment_id)

        if (
            segment is None
            or segment.document_id != document_id
            or segment.dataset_id != dataset_id
            or segment.account_id != account.id
        ):
            raise NotFoundException("片段不存在")

        return segment

    def update_segment_enabled(
        self,
        dataset_id: UUID,
        document_id: UUID,
        segment_id: UUID,
        enabled: bool,
        account: Account,
    ) -> Segment:
        """根据传递的信息更新片段的启用状态"""

        # 获取片段信息并校验权限
        segment = self.get(Segment, segment_id)

        if (
            segment is None
            or segment.document_id != document_id
            or segment.dataset_id != dataset_id
            or segment.account_id != account.id
        ):
            raise NotFoundException("片段不存在")

        # 判断文档状态是否处于可启用/禁用的环境
        if segment.status != SegmentStatus.COMPLETED:
            raise FailException("文档状态异常，无法启用/禁用")

        # 判断更新的状态与数据库中的状态是否一致，如果是，抛出错误
        if segment.enabled == enabled:
            raise FailException("片段状态无需更新")

        # 获取更新片段启用状态锁并上锁检测
        cache_key = LOCK_SEGMENT_UPDATE_ENABLED.format(segment_id=segment_id)
        cache_result = self.redis_client.get(cache_key)
        if cache_result is not None:
            raise FailException("片段状态更新中，请勿重复操作")

        # 上锁并更新对应数据，涵盖：pgsql记录、weaviate、关键词表
        with self.redis_client.lock(cache_key, timeout=LOCK_EXPIRE_TIME):
            try:
                # 修改pgsql数据库中的文档片段状态
                self.update(
                    segment,
                    enabled=enabled,
                    disabled_at=None if enabled else datetime.now(),
                )

                # 更新关键词表的对应信息，有可能新增，也有可能删除
                document = segment.document
                if enabled is True and document.enabled is True:
                    self.keyword_table_service.add_keyword_table_from_ids(
                        dataset_id, [segment.id]
                    )
                else:
                    self.keyword_table_service.delete_keyword_table_from_ids(
                        dataset_id, [segment.id]
                    )

                # 同步处理weaviate中的数据
                self.vector_database_service.collection.data.update(
                    uuid=segment.node_id, properties={"segment_enabled": enabled}
                )

            except Exception as e:
                logging.exception(
                    f"片段状态更新失败，segment_id: {segment_id},错误信息：{str(e)}"
                )
                self.update(
                    segment,
                    error=str(e),
                    status=SegmentStatus.ERROR,
                    enabled=False,
                    disabled_at=datetime.now(),
                    stopped_at=datetime.now(),
                )
                raise FailException("片段状态更新失败")

    def update_segment(
        self,
        dataset_id: UUID,
        document_id: UUID,
        segment_id: UUID,
        req: UpdateSegmentReq,
        account: Account,
    ) -> Segment:
        """根据传递的信息更新指定的文档片段信息"""

        # 1.获取片段信息并校验权限
        segment = self.get(Segment, segment_id)
        if (
            segment is None
            or segment.account_id != account.id
            or segment.dataset_id != dataset_id
            or segment.document_id != document_id
        ):
            raise NotFoundException("该文档片段不存在，或无权限修改，请核实后重试")

        # 2.判断文档片段是否处于可修改的环境
        if segment.status != SegmentStatus.COMPLETED:
            raise FailException("当前片段不可修改状态，请稍后尝试")

        # 3.检测是否传递了keywords，如果没有传递的话，调用jieba服务生成关键词
        if req.keywords.data is None or len(req.keywords.data) == 0:
            req.keywords.data = self.jieba_service.extract_keywords(
                req.content.data, 10
            )

        # 4.计算新内容hash值，用于判断是否需要更新向量数据库以及文档详情
        new_hash = generate_text_hash(req.content.data)
        required_update = segment.hash != new_hash

        try:
            # 5.更新segment表记录
            self.update(
                segment,
                keywords=req.keywords.data,
                content=req.content.data,
                hash=new_hash,
                character_count=len(req.content.data),
                token_count=self.embeddings_service.calculate_token_count(
                    req.content.data
                ),
            )

            # 7.更新片段归属关键词信息
            self.keyword_table_service.delete_keyword_table_from_ids(
                dataset_id, [segment_id]
            )
            self.keyword_table_service.add_keyword_table_from_ids(
                dataset_id, [segment_id]
            )

            # 8.检测是否需要更新文档信息以及向量数据库
            if required_update:
                # 7.更新文档信息，涵盖字符总数、token总次数
                document = segment.document
                document_character_count, document_token_count = self.db.session.query(
                    func.coalesce(func.sum(Segment.character_count), 0),
                    func.coalesce(func.sum(Segment.token_count), 0),
                ).first()
                self.update(
                    document,
                    character_count=document_character_count,
                    token_count=document_token_count,
                )

                # 9.更新向量数据库对应记录
                self.vector_database_service.collection.data.update(
                    uuid=str(segment.node_id),
                    properties={
                        "text": req.content.data,
                    },
                    vector=self.embeddings_service.embeddings.embed_query(
                        req.content.data
                    ),
                )
        except Exception as e:
            logging.exception(
                f"更新文档片段记录失败, segment_id: {segment}, 错误信息: {str(e)}"
            )
            raise FailException("更新文档片段记录失败，请稍后尝试")

        return segment

    def delete_segment(
        self, dataset_id: UUID, document_id: UUID, segment_id: UUID, account: Account
    ) -> Segment:
        """根据传递的信息删除指定的文档片段,该服务为同步方法"""

        # 获取片段信息并校验权限
        segment = self.get(Segment, segment_id)

        if (
            segment is None
            or segment.document_id != document_id
            or segment.dataset_id != dataset_id
            or segment.account_id != account.id
        ):
            raise NotFoundException("片段不存在")

        # 判断文档是否处于可以删除的状态，只有COMPLETED/ERROR状态的文档才可以删除
        if segment.status not in [SegmentStatus.COMPLETED, SegmentStatus.ERROR]:
            raise FailException("文档状态异常，无法删除")

        # 删除文档片段并获取文档信息
        document = segment.document
        self.delete(segment)

        # 同步删除关键词表中属于该片段的关键词信息
        self.keyword_table_service.delete_keyword_table_from_ids(
            dataset_id, [segment_id]
        )

        # 同步删除向量数据库存储的记录
        try:
            self.vector_database_service.collection.data.delete_by_id(
                str(segment.node_id)
            )
        except Exception as e:
            logging.exception(
                f"删除文档片段失败，segment_id: {segment_id}, 错误信息: {str(e)}"
            )
            raise FailException("删除文档片段失败")

        # 更新文档信息，涵盖字符总数，token总数
        # 重新计算片段的字符总数以及token总数
        document_character_count, document_token_count = self.db.session.query(
            func.coalesce(func.sum(Segment.character_count), 0),
            func.coalesce(func.sum(Segment.token_count), 0),
        ).first()

        # 更新文档的字符总数以及token总数
        self.update(
            document,
            character_count=document_character_count,
            token_count=document_token_count,
        )

        return segment
