import logging
import time
from uuid import UUID
from celery import shared_task
from flask import current_app


@shared_task
def demo_task(id: UUID) -> str:
    """示例任务"""
    logging.info("睡眠5秒")
    time.sleep(5)
    logging.info(f"id的值为{id}")
    logging.info(f"当前app的配置为{current_app.config}")
    return "success task"
