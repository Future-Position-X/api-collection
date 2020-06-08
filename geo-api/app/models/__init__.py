from app import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry
import uuid

from sqlalchemy_mixins import ActiveRecordMixin, SmartQueryMixin, ReprMixin, SerializeMixin, \
    ModelNotFoundError


class FPXActiveRecordMixin(ActiveRecordMixin):
    __abstract__ = True

    @classmethod
    def first_or_fail(cls, **kwargs):
        result = cls.where(**kwargs).first()
        if result:
            return result
        else:
            raise ModelNotFoundError("{} with matching '{}' was not found"
                                     .format(cls.__name__, kwargs))

class FPXTimestampsMixin:
    __abstract__ = True

    __datetime_callback__ = db.func.now

    created_at = db.Column(db.DateTime,
                           server_default=db.text('now()'),
                           nullable=False)

    updated_at = db.Column(db.DateTime,
                           server_default=db.text('now()'),
                           nullable=False)

@db.event.listens_for(FPXTimestampsMixin, 'before_update', propagate=True)
def _receive_before_update(mapper, connection, target):
    """Listen for updates and update `updated_at` column."""
    target.updated_at = target.__datetime_callback__()


class BaseModel2(db.Model, FPXActiveRecordMixin, SmartQueryMixin, ReprMixin, SerializeMixin, FPXTimestampsMixin):
    __abstract__ = True

    revision = db.Column(db.Integer, server_default=db.text('1'), nullable=False)

    __mapper_args__ = {
        "version_id_col": revision
    }

    pass


class Provider(BaseModel2):
    __tablename__ = 'providers'

    uuid = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"), unique=True,
                     nullable=False)
    name = db.Column(db.Text(), unique=True)

    collections = db.relationship('Collection', backref='provider', lazy=True)


class User(BaseModel2):
    __tablename__ = 'users'

    uuid = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"), unique=True,
                     nullable=False)
    email = db.Column(db.Text(), unique=True)
    password = db.Column(db.Text())

    provider_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('providers.uuid'), index=True, nullable=False)


class Collection(BaseModel2):
    __tablename__ = 'collections'
    __table_args__ = (
        db.UniqueConstraint('provider_uuid', 'name'),)
    uuid = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = db.Column(db.Text())
    is_public = db.Column(db.Boolean, default=False)

    items = db.relationship('Item', backref='collection', lazy=True)

    provider_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('providers.uuid'), index=True, nullable=False)


def append_property_filter_to_where_clause(where_clause, filter, execute_dict):
    params = filter.split(",")

    for i, p in enumerate(params):
        tokens = p.split("=")
        name = "name_" + str(i)
        value = "value_" + str(i)

        where_clause += " properties->>%(" + \
                        name + ")s = %(" + value + ")s"
        execute_dict[name] = tokens[0]
        execute_dict[value] = tokens[1]

        if i < (len(params) - 1):
            where_clause += " AND"

    return where_clause


class Item(BaseModel2):
    __tablename__ = 'items'

    uuid = db.Column(UUID(as_uuid=True), primary_key=True, server_default=db.text("gen_random_uuid()"), unique=True,
                     nullable=False)
    geometry = db.Column(Geometry(geometry_type='GEOMETRY'))
    properties = db.Column(JSONB)

    collection_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('collections.uuid'), index=True, nullable=False)
    provider_uuid = db.Column(UUID(as_uuid=True), db.ForeignKey('providers.uuid'), index=True, nullable=False)

    @classmethod
    def find_by_collection_uuid(cls, collection_uuid, filters):
        where = "collection_uuid = :collection_uuid"

        if filters["valid"]:
            where += " AND ST_IsValid(geometry)"

        exec_dict = {
            "collection_uuid": collection_uuid,
            "offset": filters["offset"],
            "limit": filters["limit"]
        }

        if filters["property_filter"] is not None:
            where += " AND "
            where = append_property_filter_to_where_clause(
                where, filters["property_filter"], exec_dict)

        result = cls.query.from_statement(db.text("""
            SELECT uuid,
                provider_uuid,
                collection_uuid,
                properties,
                ST_AsGeoJSON(geometry)::jsonb as geometry
            FROM items
            WHERE """ + where + """
                OFFSET :offset
                LIMIT :limit
            """)).params(exec_dict).all()

        return result

    @classmethod
    def copy_items(cls, src_collection_uuid, dest_collection_uuid, provider_uuid):
        result = cls.session().execute("""
            INSERT INTO items (provider_uuid, collection_uuid, geometry, properties) 
                SELECT :provider_uuid, :dest_collection_uuid, geometry, properties
                FROM items WHERE collection_uuid = :src_collection_uuid
            """, {
            "provider_uuid": provider_uuid,
            "src_collection_uuid": src_collection_uuid,
            "dest_collection_uuid": dest_collection_uuid
        })