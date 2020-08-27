from flask import request
from flask_jwt_extended import jwt_required, jwt_optional
from flask_restx import Resource, fields

from app import api
from app.dto import UserDTO
from app.handlers.flask import (
    get_provider_uuid_from_request,
    get_user_uuid_from_request,
)
from app.services.user import get_users, create_user, get_user, update_user, delete_user

ns = api.namespace("users", "User operations")

user_model = api.model(
    "User",
    {
        "uuid": fields.String(description="uuid"),
        "provider_uuid": fields.String(description="provider_uuid"),
        "email": fields.String(description="email"),
        "revision": fields.String(description="revision"),
        "created_at": fields.String(description="created_at"),
        "updated_at": fields.String(description="updated_at"),
    },
)

create_user_model = api.model(
    "CreateUser",
    {
        "email": fields.String(description="email"),
        "password": fields.String(description="password"),
    },
)

update_user_model = api.model(
    "UpdateUser", {"password": fields.String(description="password")}
)

get_uuid_model = api.model("GetUuid", {"uuid": fields.String(description="uuid")})


@ns.route("/")
class UserList(Resource):
    @jwt_optional
    @ns.doc("get_users", security=None)
    @ns.marshal_list_with(user_model)
    def get(self):
        users = get_users()
        return users

    @jwt_optional
    @ns.doc("create_user", security=None)
    @ns.expect(create_user_model)
    @ns.marshal_with(user_model, code=201)
    def post(self):
        print(request.get_json())
        user = UserDTO(**request.get_json())
        try:
            user = create_user(user)
            return user, 201
        except ValueError:
            return "", 400


@ns.route("/<uuid:user_uuid>")
@ns.response(404, "User not found")
@ns.param("user_uuid", "The user identifier")
class UserApi(Resource):
    @jwt_optional
    @ns.doc("get_user", security=None)
    @ns.marshal_with(user_model)
    def get(self, user_uuid):
        user = get_user(user_uuid)
        return user

    @jwt_required
    @ns.doc("update_user")
    @ns.expect(update_user_model)
    def put(self, user_uuid):
        provider_uuid = get_provider_uuid_from_request()
        user_dict = request.get_json()
        user_update = UserDTO(**user_dict)
        update_user(provider_uuid, user_uuid, user_update)
        return "", 204

    @jwt_required
    @ns.doc("delete_user")
    def delete(self, user_uuid):
        provider_uuid = get_provider_uuid_from_request()
        delete_user(provider_uuid, user_uuid)
        return "", 204


@ns.route("/uuid")
class UserUuidApi(Resource):
    @jwt_required
    @ns.doc("get_user_uuid", security=None)
    @ns.marshal_with(get_uuid_model)
    def get(self):
        user_uuid = get_user_uuid_from_request()
        return {"uuid": user_uuid}, 200
