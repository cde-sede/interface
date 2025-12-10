from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from ._base_api import ABCApi, describe, register
from ._manager import Manager
from flask import Blueprint, request, jsonify
from ..plugins.auth import Plugin as AuthPlugin


class AuthAPI(ABCApi):
	def __init__(self, manager: Manager[ABCApi], parent: ABCApi):
		self.manager = manager
		self.parent = parent
		self.bp = self.create_blueprint("auth", parent=parent, url_prefix="/auth")
		self.auth: AuthPlugin = cast(AuthPlugin, self.manager.get('plugins.auth'))

		self.add_rules(self.bp)

	@register("/register", methods=["POST"])
	@describe(
		"Register a new user",
		"route",
		params={
			"username": {
				"type": "string",
				"required": True,
				"description": "Username for the new account",
				"in": "body",
			},
			"email": {
				"type": "string",
				"required": True,
				"description": "Email address for the new account",
				"in": "body",
			},
			"password": {
				"type": "string",
				"required": True,
				"description": "Password (minimum 8 characters)",
				"in": "body",
			}
		},
		method="POST"
	)
	def register_user(self):
		"""Register a new user account."""
		data = request.get_json()

		if not data:
			return jsonify({"error": "No data provided"}), 400

		username = data.get("username")
		email = data.get("email")
		password = data.get("password")

		if not all([username, email, password]):
			return jsonify({"error": "Missing required fields"}), 400

		result = self.auth.register_user(username, email, password)
		print(isinstance(result, self.auth.RegistrationError))
		print(isinstance(result, self.auth.RegistrationSuccess))

		match result:
			case self.auth.RegistrationSuccess(user_id=uid, username=uname):
				return jsonify({
					"message": "User registered successfully",
					"user_id": uid,
					"username": uname
				}), 201
			case self.auth.RegistrationError(error=err):
				status_code = 409 if "already exists" in err else 400
				return jsonify({"error": err}), status_code

	@register("/login", methods=["POST"])
	@describe(
		"Authenticate user and receive JWT token",
		"route",
		params={
			"username": {
				"type": "string",
				"required": True,
				"description": "Username",
				"in": "body",
			},
			"password": {
				"type": "string",
				"required": True,
				"description": "Password",
				"in": "body",
			}
		},
		method="POST"
	)
	def login(self):
		"""Authenticate user and return JWT token."""
		data = request.get_json()

		if not data:
			return jsonify({"error": "No data provided"}), 400

		username = data.get("username")
		password = data.get("password")

		if not all([username, password]):
			return jsonify({"error": "Missing username or password"}), 400

		result = self.auth.authenticate_user(username, password)

		match result:
			case self.auth.AuthenticationSuccess(token=token, user=user):
				return jsonify({
					"message": "Login successful",
					"token": token,
					"user": {
						"id": user.id,
						"username": user.username,
						"email": user.email,
						"created_at": user.created_at,
						"last_login": user.last_login
					}
				}), 200
			case self.auth.AuthenticationError(error=err):
				return jsonify({"error": err}), 401

	@register("/verify", methods=["GET"])
	@describe(
		"Verify JWT token",
		"route",
		params={
			"Authorization": {
				"type": "string",
				"required": True,
				"description": "Bearer token in format 'Bearer <token>'",
				"in": "header",
			}
		},
		method="GET"
	)
	def verify(self):
		"""Verify JWT token from Authorization header."""
		auth_header = request.headers.get("Authorization")

		if not auth_header:
			return jsonify({"error": "No authorization header"}), 401

		try:
			token = auth_header.split(" ")[1] if " " in auth_header else auth_header
		except IndexError:
			return jsonify({"error": "Invalid authorization header"}), 401

		user = self.auth.verify_token(token)

		if not user:
			return jsonify({"error": "Invalid or expired token"}), 401

		return jsonify({
			"valid": True,
			"user": {
				"id": user.id,
				"username": user.username,
				"email": user.email
			}
		}), 200

	@register("/change-password", methods=["POST"])
	@describe(
		"Change user password",
		"route",
		params={
			"Authorization": {
				"type": "string",
				"required": True,
				"description": "Bearer token in format 'Bearer <token>'",
				"in": "header",
			},
			"old_password": {
				"type": "string",
				"required": True,
				"description": "Current password",
				"in": "body",
			},
			"new_password": {
				"type": "string",
				"required": True,
				"description": "New password (minimum 8 characters)",
				"in": "body",
			}
		},
		method="POST"
	)
	def change_password(self):
		"""Change password for authenticated user."""
		auth_header = request.headers.get("Authorization")

		if not auth_header:
			return jsonify({"error": "No authorization header"}), 401

		token = auth_header.split(" ")[1] if " " in auth_header else auth_header
		user = self.auth.verify_token(token)

		if not user:
			return jsonify({"error": "Invalid or expired token"}), 401

		data = request.get_json()

		if not data:
			return jsonify({"error": "No data provided"}), 400

		old_password = data.get("old_password")
		new_password = data.get("new_password")

		if not all([old_password, new_password]):
			return jsonify({"error": "Missing required fields"}), 400

		result = self.auth.change_password(user.id, old_password, new_password)

		match result:
			case self.auth.OperationSuccess():
				return jsonify({"message": "Password changed successfully"}), 200
			case self.auth.OperationError(error=err):
				status_code = 404 if "not found" in err else 400
				return jsonify({"error": err}), status_code

	@register("/user/<int:user_id>", methods=["GET"])
	@describe(
		"Get user information",
		"route",
		params={
			"Authorization": {
				"type": "string",
				"required": True,
				"description": "Bearer token in format 'Bearer <token>'",
				"in": "header",
			},
			"user_id": {
				"type": "integer",
				"required": True,
				"description": "User ID",
				"in": "path",
			}
		},
		method="GET"
	)
	def get_user(self, user_id: int):
		"""Get user information by ID (requires authentication)."""
		auth_header = request.headers.get("Authorization")

		if not auth_header:
			return jsonify({"error": "No authorization header"}), 401

		token = auth_header.split(" ")[1] if " " in auth_header else auth_header
		current_user = self.auth.verify_token(token)

		if not current_user:
			return jsonify({"error": "Invalid or expired token"}), 401

		user = self.auth.get_user_by_id(user_id)

		if not user:
			return jsonify({"error": "User not found"}), 404

		return jsonify({
			"id": user.id,
			"username": user.username,
			"email": user.email,
			"created_at": user.created_at,
			"last_login": user.last_login
		}), 200

	@register("/users", methods=["GET"])
	@describe(
		"List all users",
		"route",
		params={
			"Authorization": {
				"type": "string",
				"required": True,
				"description": "Bearer token in format 'Bearer <token>'",
				"in": "header",
			},
			"limit": {
				"type": "integer",
				"required": False,
				"description": "Maximum number of users to return (default: 100)",
				"in": "query",
			},
			"offset": {
				"type": "integer",
				"required": False,
				"description": "Number of users to skip (default: 0)",
				"in": "query",
			}
		},
		method="GET"
	)
	def list_users(self):
		"""List users with pagination (requires authentication)."""
		auth_header = request.headers.get("Authorization")

		if not auth_header:
			return jsonify({"error": "No authorization header"}), 401

		token = auth_header.split(" ")[1] if " " in auth_header else auth_header
		current_user = self.auth.verify_token(token)

		if not current_user:
			return jsonify({"error": "Invalid or expired token"}), 401

		limit = request.args.get("limit", 100, type=int)
		offset = request.args.get("offset", 0, type=int)

		users = self.auth.list_users(limit=limit, offset=offset)

		return jsonify({
			"users": [
				{
					"id": user.id,
					"username": user.username,
					"email": user.email,
					"created_at": user.created_at,
					"last_login": user.last_login
				}
				for user in users
			],
			"limit": limit,
			"offset": offset,
			"count": len(users)
		}), 200

	@register("/", methods=["GET"])
	@describe("Auth API information")
	def index(self):
		"""Auth API index with available endpoints."""
		return jsonify({
			"name": "Authentication API",
			"version": "1.0",
			"endpoints": {
				"POST /auth/register": "Register a new user",
				"POST /auth/login": "Login and receive JWT token",
				"GET /auth/verify": "Verify JWT token",
				"POST /auth/change-password": "Change user password",
				"GET /auth/user/<id>": "Get user information",
				"GET /auth/users": "List all users"
			}
		}), 200

	@property
	def name(self) -> str:
		return "auth"

	@property
	def blueprint(self) -> Blueprint:
		return self.bp


def setup(manager: Manager[ABCApi], /):
	parent = require('v1')
	return AuthAPI(manager, parent)

if TYPE_CHECKING:
	setup = validate_setup(setup)
