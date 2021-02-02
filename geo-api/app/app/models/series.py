from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import relationship

from app.models.base_model import BaseModel

from ..dto import SeriesDTO

if TYPE_CHECKING:
    from .item import Item  # noqa: F401
    from .metric import Metric  # noqa: F401


class Series(BaseModel):
    __tablename__ = "series"
    uuid = sa.Column(
        pg.UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    item_uuid = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("items.uuid", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    data = sa.Column(pg.JSONB)

    item = relationship("Item", back_populates="series")
    metrics = relationship(
        "Metric", back_populates="series", cascade="all, delete", passive_deletes=True
    )

    @classmethod
    def find_by_item_uuid(cls, item_uuid: UUID) -> List[SeriesDTO]:
        query = cls.query.filter(cls.item_uuid == item_uuid)
        res = query.all()
        return res
