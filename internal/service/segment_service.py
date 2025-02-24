from datetime import datetime
import logging
from uuid import UUID
from injector import inject
from dataclasses import dataclass

from sqlalchemy import asc
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
from internal.schema.segment_schema import (
    GetSegmentsWithPageReq,
)
from internal.model import Segment, Document
from pkg.paginator import Paginator
from internal.exception import NotFoundException, FailException
from internal.entity.dataset_entity import SegmentStatus
from internal.entity.cache_entity import LOCK_SEGMENT_UPDATE_ENABLED, LOCK_EXPIRE_TIME
from redis import Redis
from .keyword_table_service import KeywordTableService
from .vector_database_service import VectorDatabaseService


@inject
@dataclass
class SegmentService(BaseService):
    """片段服务"""

    db: SQLAlchemy
    redis_client: Redis
    keyword_table_service: KeywordTableService
    vector_database_service: VectorDatabaseService

    def get_segments_with_page(
        self, dataset_id: UUID, document_id: UUID, req: GetSegmentsWithPageReq
    ) -> tuple[list[Segment], Paginator]:
        """根据传递的信息获取片段列表分页数据"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 获取文档并校验权限
        document = self.get(Document, document_id)
        print(document.account_id)
        if (
            document is None
            or document.dataset_id != dataset_id
            or str(document.account_id) != account_id
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
        self, dataset_id: UUID, document_id: UUID, segment_id: UUID
    ) -> Segment:
        """根据传递的信息获取片段信息"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 获取片段信息并校验权限
        segment = self.get(Segment, segment_id)

        if (
            segment is None
            or segment.document_id != document_id
            or segment.dataset_id != dataset_id
            or str(segment.account_id) != account_id
        ):
            raise NotFoundException("片段不存在")

        return segment

    def update_segment_enabled(
        self, dataset_id: UUID, document_id: UUID, segment_id: UUID, enabled: bool
    ) -> Segment:
        """根据传递的信息更新片段的启用状态"""
        # todo:等待授权认证模块完成后再进行开发
        account_id = "15fd2840-e294-4413-83d0-e083e9a7bc6b"

        # 获取片段信息并校验权限
        segment = self.get(Segment, segment_id)

        if (
            segment is None
            or segment.document_id != document_id
            or segment.dataset_id != dataset_id
            or str(segment.account_id) != account_id
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
