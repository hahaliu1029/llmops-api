import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    UUID,
    String,
    Text,
    DateTime,
    PrimaryKeyConstraint,
    Index,
)
from internal.extention.database_extension import db


class App(db.Model):
    """应用表"""

    __tablename__ = "app"

    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_id"),
        Index("idx_app_account_id", "account_id"),
    )

    id = Column(UUID, default=uuid.uuid4, nullable=False)
    name = Column(String(255), default="", nullable=False)
    account_id = Column(UUID, nullable=False)
    icon = Column(String(255), default="", nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(255), default="normal", nullable=False)
    updated_at = Column(
        DateTime, default=datetime.now, onupdate=datetime.now, nullable=False
    )
    created_at = Column(DateTime, default=datetime.now, nullable=False)
