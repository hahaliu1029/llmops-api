from uuid import UUID
from celery import shared_task


@shared_task
def delete_dataset(dataset_id: UUID) -> None:
    """根据传递的知识库ID删除知识库"""
    from app.http.module import injector
    from internal.service.indexing_service import IndexingService

    indexing_service = injector.get(IndexingService)
    indexing_service.delete_dataset(dataset_id)
