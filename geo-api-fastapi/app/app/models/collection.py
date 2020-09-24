import uuid

import sqlalchemy as sa
import sqlalchemy_mixins
from sqlalchemy import or_, and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.dto import InternalUserDTO, Access
from app.models import BaseModel
from app.models.acl import ACL


class Collection(BaseModel):
    __tablename__ = "collections"
    __table_args__ = (sa.UniqueConstraint("provider_uuid", "name"),)
    uuid = sa.Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    name = sa.Column(sa.Text())
    is_public = sa.Column(sa.Boolean, default=False)

    items = relationship("Item", lazy=True)

    provider_uuid = sa.Column(
        UUID(as_uuid=True), sa.ForeignKey("providers.uuid"), index=True, nullable=False
    )

    @classmethod
    def writeable_query(cls, user: InternalUserDTO):
        user_uuid = user.uuid
        provider_uuid = user.provider_uuid
        q = (
            cls.session.query(cls.uuid)
            .outerjoin(
                ACL,
                or_(
                    ACL.granted_provider_uuid == provider_uuid,
                    ACL.granted_user_uuid == user_uuid,
                ),
            )
            .filter(
                or_(
                    cls.provider_uuid == provider_uuid,
                    and_(
                        ACL.collection_uuid == cls.uuid,
                        ACL.access == Access.WRITE.value,
                    ),
                )
            )
        )
        return q

    @classmethod
    def readable_query(cls, user: InternalUserDTO):
        user_uuid = user.uuid
        provider_uuid = user.provider_uuid
        q = (
            cls.session.query(cls.uuid)
            .outerjoin(
                ACL,
                or_(
                    ACL.granted_provider_uuid == provider_uuid,
                    ACL.granted_user_uuid == user_uuid,
                ),
            )
            .filter(
                or_(
                    cls.provider_uuid == provider_uuid,
                    cls.is_public == True,  # noqa: E712
                    and_(
                        ACL.collection_uuid == cls.uuid, ACL.access == Access.READ.value
                    ),
                )
            )
        )
        return q

    # TODO: Investigate if this should be done with JOIN instead of SUBQUERY
    @classmethod
    def find_readable(cls, user: InternalUserDTO):
        readable_sq = cls.readable_query(user).subquery()
        q = cls.query.filter(cls.uuid.in_(readable_sq))
        res = q.all()

        return res

    # TODO: Investigate if this should be done with JOIN instead of SUBQUERY
    @classmethod
    def find_readable_or_fail(cls, user: InternalUserDTO, collection_uuid):
        readable_sq = cls.readable_query(user).subquery()
        q = cls.query.filter(cls.uuid == collection_uuid)
        q = q.filter(cls.uuid.in_(readable_sq))
        res = q.first()

        if res is None:
            raise sqlalchemy_mixins.ModelNotFoundError
        return res

    # TODO: Investigate if this should be done with JOIN instead of SUBQUERY
    @classmethod
    def find_writeable_or_fail(cls, user: InternalUserDTO, collection_uuid):
        writeable_sq = cls.writeable_query(user).subquery()
        q = cls.query.filter(cls.uuid == collection_uuid)
        q = q.filter(cls.uuid.in_(writeable_sq))
        res = q.first()

        if res is None:
            raise sqlalchemy_mixins.ModelNotFoundError
        return res
