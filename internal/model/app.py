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
    text,
)
from internal.extention.database_extension import db


class App(db.Model):
    """应用表"""

    __tablename__ = "app"

    __table_args__ = (
        PrimaryKeyConstraint("id", name="pk_app_id"),
        Index("idx_app_account_id", "account_id"),
    )

    id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
    name = Column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    account_id = Column(UUID, server_default=text("''::character varying"))
    icon = Column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    description = Column(Text, nullable=False, server_default=text("''::text"))
    status = Column(
        String(255), nullable=False, server_default=text("''::character varying")
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(0)"),
        server_onupdate=text("CURRENT_TIMESTAMP(0)"),
    )
    created_at = Column(
        DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP(0)")
    )
    a_id = Column(UUID, nullable=False, server_default=text("uuid_generate_v4()"))
