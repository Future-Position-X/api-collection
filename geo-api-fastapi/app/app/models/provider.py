import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import RelationshipProperty, relationship

from app.models import Collection
from app.models.base_model import BaseModel


class Provider(BaseModel):
    __tablename__ = "providers"

    uuid = sa.Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
        unique=True,
        nullable=False,
    )
    name = sa.Column(sa.Text(), unique=True)

    collections: RelationshipProperty[Collection] = relationship(
        "Collection", backref="provider", lazy=True
    )
