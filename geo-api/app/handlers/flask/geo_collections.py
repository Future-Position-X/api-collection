from flask import request
from flask_jwt_extended import jwt_required
from flask_restx import Resource, fields

from app import api
from app.dto import CollectionDTO
from app.handlers.flask import (
    get_provider_uuid_from_request,

)
from app.services.collection import (
    copy_collection_from,
    get_all_accessable_collections, create_collection, get_collection_by_uuid, delete_collection_by_uuid,
    update_collection_by_uuid
)

ns = api.namespace('collections', 'Collection operations')

collection_model = api.model('Collection', {
    'uuid': fields.String(description='uuid'),
    'provider_uuid': fields.String(description='provider_uuid'),
    'name': fields.String(description='name'),
    'is_public': fields.String(description='is_public'),
    'revision': fields.String(description='revision'),
    'created_at': fields.String(description='created_at'),
    'updated_at': fields.String(description='updated_at'),
})

create_collection_model = api.model('CreateCollection', {
    'name': fields.String(description='name'),
    'is_public': fields.String(description='is_public'),
})

update_collection_model = api.model('UpdateCollection', {
    'name': fields.String(description='name'),
    'is_public': fields.String(description='is_public'),
})


@ns.route('/')
class CollectionListApi(Resource):
    @ns.doc('list_collections', security=None)
    @ns.marshal_list_with(collection_model)
    def get(self):
        provider_uuid = get_provider_uuid_from_request()
        collections = get_all_accessable_collections(provider_uuid)
        return collections

    @jwt_required
    @ns.doc('create_collection')
    @ns.expect(create_collection_model)
    @ns.marshal_with(collection_model, 201)
    def post(self):
        provider_uuid = get_provider_uuid_from_request()
        collection = CollectionDTO(**request.get_json())
        collection = create_collection(provider_uuid, collection)
        return collection, 201


@ns.route('/<uuid:collection_uuid>')
@ns.response(404, 'Collection not found')
@ns.param('collection_uuid', 'The collection identifier')
class CollectionApi(Resource):
    @ns.doc('get_collection', security=None)
    @ns.marshal_with(collection_model)
    def get(self, collection_uuid):
        provider_uuid = get_provider_uuid_from_request()
        collection = get_collection_by_uuid(provider_uuid, collection_uuid)
        return collection

    @jwt_required
    @ns.doc('delete_collection')
    @ns.response(204, 'Collection deleted')
    def delete(self, collection_uuid):
        provider_uuid = get_provider_uuid_from_request()
        delete_collection_by_uuid(provider_uuid, collection_uuid)
        return '', 204

    @jwt_required
    @ns.doc('update_collection')
    @ns.expect(update_collection_model)
    @ns.marshal_with(collection_model)
    @ns.response(200, 'Collection updated')
    def put(self, collection_uuid):
        provider_uuid = get_provider_uuid_from_request()
        collection_update = CollectionDTO(**request.get_json())
        collection = update_collection_by_uuid(provider_uuid, collection_uuid, collection_update)
        return collection


@ns.route('/<uuid:src_collection_uuid>/copy')
@ns.route('/<uuid:src_collection_uuid>/copy/<uuid:dst_collection_uuid>')
@ns.param('src_collection_uuid', 'The src collection identifier')
@ns.param('dst_collection_uuid', 'The dst collection identifier')
class CollectionCopyApi(Resource):
    @jwt_required
    @ns.doc('copy_collection')
    @ns.marshal_with(collection_model, 201)
    def post(self, src_collection_uuid, dst_collection_uuid=None):
        provider_uuid = get_provider_uuid_from_request()
        try:
            collection = copy_collection_from(provider_uuid, src_collection_uuid, dst_collection_uuid)
        except PermissionError as e:
            return '', 403

        return collection, 201
