from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import desc
from sqlalchemy.dialects import postgresql as pg
from sqlalchemy.orm import relationship

from app.dto import SeriesDTO
from app.models.base_model import BaseModel

if TYPE_CHECKING:
    from .series import Series  # noqa: F401


class Metric(BaseModel):
    __tablename__ = "metrics"
    __table_args__ = (sa.PrimaryKeyConstraint("series_uuid", "ts"),)
    ts = sa.Column(sa.DateTime, server_default=sa.text("now()"), nullable=False)
    series_uuid = sa.Column(
        pg.UUID(as_uuid=True),
        sa.ForeignKey("series.uuid", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    data = sa.Column(pg.JSONB)

    series = relationship("Series", back_populates="metrics")

    @classmethod
    def find_by_series_uuid(cls, series_uuid: UUID, filters: dict) -> List[SeriesDTO]:
        where, exec_dict = cls.create_where(filters)
        query = (
            cls.query.filter(cls.series_uuid == series_uuid)
            .filter(sa.text(where))
            .params(exec_dict)
        )
        res = (
            query.order_by(desc(Metric.ts))
            .limit(filters["limit"])
            .offset(filters["offset"])
            .all()
        )
        return res

    @staticmethod
    def create_where(filters: dict) -> Tuple[str, Dict[str, Optional[Any]]]:
        where = """
        (
            1=1
        )"""

        exec_dict = {"offset": filters["offset"], "limit": filters["limit"]}

        if filters["data_filter"] is not None:
            where += " AND "
            where = Metric.append_data_filter_to_where_clause(
                where, filters["data_filter"], exec_dict
            )

        if filters["filter"] is not None:
            where += " AND "
            where = Metric.append_filter_to_where_clause(
                where, filters["filter"], exec_dict
            )

        return where, exec_dict

    @staticmethod
    def append_filter_to_where_clause(
        where_clause: str, data_filter: str, execute_dict: dict
    ) -> str:
        params = data_filter.split(",")

        for i, p in enumerate(params):
            operator_str = "="
            match = re.search("(<=|>=|!=|<|>|=)", p)
            if match:
                operator_str = match.group(0)
            operators = {
                "<=": "<=",
                ">=": ">=",
                "!=": "!=",
                "<": "<",
                ">": ">",
                "=": "=",
            }
            tokens = p.split(operators[operator_str])
            value = "value_" + str(i)

            where_clause += (
                " "
                + Metric.__table__.columns[tokens[0]].__str__()
                + " "
                + operators[operator_str]
                + " :"
                + value
            )
            execute_dict[value] = tokens[1]

            if i < (len(params) - 1):
                where_clause += " AND"

        return where_clause

    @staticmethod
    def append_data_filter_to_where_clause(
        where_clause: str, data_filter: str, execute_dict: dict
    ) -> str:
        params = data_filter.split(",")

        for i, p in enumerate(params):
            operator_str = "="
            match = re.search("(<=|>=|!=|<|>|=)", p)
            if match:
                operator_str = match.group(0)
            operators = {
                "<=": "<=",
                ">=": ">=",
                "!=": "!=",
                "<": "<",
                ">": ">",
                "=": "=",
            }
            tokens = p.split(operators[operator_str])
            name = "name_" + str(i)
            value = "value_" + str(i)

            where_clause += (
                " data->>:" + name + " " + operators[operator_str] + " :" + value
            )
            execute_dict[name] = tokens[0]
            execute_dict[value] = tokens[1]

            if i < (len(params) - 1):
                where_clause += " AND"

        return where_clause
