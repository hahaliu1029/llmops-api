from uuid import UUID
from injector import inject
from dataclasses import dataclass

from internal.entity.cache_entity import (
    LOCK_EXPIRE_TIME,
    LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE,
)
from .base_service import BaseService
from pkg.sqlalchemy import SQLAlchemy
from internal.model import KeywordTable, Segment
from redis import Redis


@inject
@dataclass
class KeywordTableService(BaseService):
    """关键词表服务"""

    db: SQLAlchemy
    redis_client: Redis

    def get_keyword_table_from_dataset_id(self, dataset_id: UUID) -> KeywordTable:
        """根据传递的知识库id获取关键词表"""
        keyword_table = (
            self.db.session.query(KeywordTable)
            .filter(KeywordTable.dataset_id == dataset_id)
            .one_or_none()
        )
        if keyword_table is None:
            keyword_table = self.create(
                KeywordTable, dataset_id=dataset_id, keyword_table={}
            )
        return keyword_table

    def delete_keyword_table_from_ids(
        self, dataset_id: UUID, segment_ids: list[UUID]
    ) -> None:
        """根据知识库id和段落id删除对应关键词表中多余的数据"""
        # 更新知识库关键词表信息，并且该操作需要上锁，避免并发更新的时候出现关键词映射错误的问题
        cache_key = LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE.format(
            dataset_id=dataset_id
        )
        with self.redis_client.lock(cache_key, timeout=LOCK_EXPIRE_TIME):
            # 获取关键词表信息
            keyword_table_record = self.get_keyword_table_from_dataset_id(dataset_id)
            keyword_table = keyword_table_record.keyword_table.copy()

            # 记录需要删除的片段id和空关键词列表
            segment_ids_to_delete = set(str(segment_id) for segment_id in segment_ids)
            keywords_to_delete = set()

            # 循环遍历关键词表，执行判断与更新
            for keyword, ids in keyword_table.items():
                ids_set = set(ids)
                if segment_ids_to_delete.intersection(ids_set):
                    keyword_table[keyword] = list(
                        ids_set.difference(segment_ids_to_delete)
                    )
                    if not keyword_table[keyword]:
                        keywords_to_delete.add(keyword)

            # 检测空关键词数据并删除（关键词并没有映射任何字段id的数据）
            for keyword in keywords_to_delete:
                del keyword_table[keyword]

            # 将数据更新到关键词表中
            self.update(
                keyword_table_record,
                keyword_table=keyword_table,
            )

    def add_keyword_table_from_ids(
        self, dataset_id: UUID, segment_ids: list[UUID]
    ) -> None:
        """根据知识库id和段落id添加对应关键词表中新的数据"""
        # 更新知识库关键词表信息，并且该操作需要上锁，避免并发更新的时候出现关键词映射错误的问题
        cache_key = LOCK_KEYWORD_TABLE_UPDATE_KEYWORD_TABLE.format(
            dataset_id=dataset_id
        )
        with self.redis_client.lock(cache_key, timeout=LOCK_EXPIRE_TIME):
            # 获取当前知识库的关键词表
            keyword_table_record = self.get_keyword_table_from_dataset_id(dataset_id)
            keyword_table = {
                field: set(value)
                for field, value in keyword_table_record.keyword_table.items()
            }

            # 根据segment_ids查找片段的关键词信息
            segments = (
                self.db.session.query(Segment)
                .with_entities(Segment.id, Segment.keywords)
                .filter(Segment.id.in_(segment_ids))
                .all()
            )

            for id, keywords in segments:
                for keyword in keywords:
                    if keyword not in keyword_table:
                        keyword_table[keyword] = set()
                    keyword_table[keyword].add(str(id))

            # 更新关键词表
            self.update(
                keyword_table_record,
                keyword_table={
                    field: list(value) for field, value in keyword_table.items()
                },
            )
