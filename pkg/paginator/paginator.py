from typing import Any
import math
from flask_wtf import FlaskForm
from wtforms import IntegerField
from wtforms.validators import Optional, NumberRange
from dataclasses import dataclass
from pkg.sqlalchemy import SQLAlchemy


class PaginatorReq(FlaskForm):
    """分页请求基础类，涵盖当前页数和每页数量，如果接口需要分页，继承此类"""

    current_page = IntegerField(
        "current_page",
        default=1,
        validators=[
            Optional(),
            NumberRange(min=1, max=9999, message="current_page必须在1-9999之间"),
        ],
    )
    page_size = IntegerField(
        "page_size",
        default=20,
        validators=[
            Optional(),
            NumberRange(min=1, max=50, message="page_size必须在1-50之间"),
        ],
    )


@dataclass
class Paginator:
    """分页器"""

    total_page: int = 0  # 总页数
    total_record: int = 0  # 总记录数
    current_page: int = 1  # 当前页数
    page_size: int = 20  # 每页数量

    def __init__(self, db: SQLAlchemy, req: PaginatorReq = None):
        if req is not None:
            self.current_page = req.current_page.data
            self.page_size = req.page_size.data
        self.db = db

    def paginate(self, select) -> list[Any]:
        """分页查询"""
        # 调用paginate方法进行分页查询
        p = self.db.paginate(
            select, page=self.current_page, per_page=self.page_size, error_out=False
        )

        # 计算总页数+总记录数
        self.total_record = p.total
        self.total_page = math.ceil(p.total / self.page_size)

        return p.items


@dataclass
class PageModel:
    list: list[Any]  # 数据列表
    paginator: Paginator  # 分页器
