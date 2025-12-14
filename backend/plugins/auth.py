from typing import TYPE_CHECKING, Optional, cast, Callable, Any
if TYPE_CHECKING:
	from _injected import validate_setup

from ._base_plugin import ABCPlugin
from ._manager import Manager
from dataclasses import dataclass
import bcrypt
import jwt
import datetime
import secrets
from functools import wraps
from flask import request, jsonify, abort

from ..services.db import Service as DB
from ..services.settings import Service as Settings
from .models.users import User, UserRecord
from .models.apikeys import ApiKey, ApiKeyRecord

class AuthUtils:
	manager: Manager
	def require_user_auth(self, *args: Any, **kwargs: Any) -> bool:
		"""
		Condition function that checks if the current request is authenticated.
		Calls abort(401) if authentication fails.

		Usage:
			@cond(auth.require_auth)
			def protected_route():
				return jsonify({'message': 'Protected content'})

		Aborts with 401 if token is missing or invalid.
		Returns True if authenticated.
		"""
		assert hasattr(self, 'manager') and isinstance(self.manager, Manager)

		auth = self.manager.get[Plugin]('plugins.auth')

		token = auth._get_token_from_request()
		if not token:
			abort(401, description='Missing authentication token')

		user_data = auth.verify_token(token)
		if not user_data:
			abort(401, description='Invalid or expired token')

		return True

	def require_user_admin(self, *args: Any, **kwargs: Any) -> bool:
		"""
		Condition function that checks if the current request is authenticated
		and the user has admin privileges (level >= 1).
		Calls abort(401) if not authenticated or abort(403) if not admin.

		Usage:
			@cond(auth.require_admin)
			def admin_route():
				return jsonify({'message': 'Admin content'})

		Aborts with 401 if token is missing or invalid.
		Aborts with 403 if user is not an admin.
		Returns True if authenticated and admin.
		"""
		assert hasattr(self, 'manager') and isinstance(self.manager, Manager)

		auth = self.manager.get[Plugin]('auth')

		token = auth._get_token_from_request()
		if not token:
			abort(401, description='Missing authentication token')

		user_data = auth.verify_token(token)
		if not user_data:
			abort(401, description='Invalid or expired token')

		if user_data.level < 1:
			abort(403, description='Admin privileges required')

		return True

	def require_apikey(self, *args: Any, **kwargs: Any) -> bool:
		"""
		Condition function that checks if the current request has a valid API key.
		Calls abort(401) if API key is missing, invalid, or expired.

		Usage:
			@cond(auth.require_apikey)
			def api_route():
				return jsonify({'message': 'API key authenticated'})

		Aborts with 401 if API key is missing, invalid, or expired.
		Returns True if API key is valid.
		"""
		assert hasattr(self, 'manager') and isinstance(self.manager, Manager)

		auth = self.manager.get[Plugin]('auth')

		api_key = auth._get_apikey_from_request()
		if not api_key:
			abort(401, description='Missing API key')

		key_data = auth.verify_apikey(api_key)
		if not key_data:
			abort(401, description='Invalid or expired API key')

		return True

	def require_apikey_admin(self, *args: Any, **kwargs: Any) -> bool:
		"""
		Condition function that checks if the current request has a valid API key
		with admin privileges (level >= 1).
		Calls abort(401) if API key is missing/invalid or abort(403) if not admin.

		Usage:
			@cond(auth.require_apikey_admin)
			def admin_api_route():
				return jsonify({'message': 'Admin API key authenticated'})

		Aborts with 401 if API key is missing, invalid, or expired.
		Aborts with 403 if API key does not have admin privileges.
		Returns True if API key is valid and has admin privileges.
		"""
		assert hasattr(self, 'manager') and isinstance(self.manager, Manager)

		auth = self.manager.get[Plugin]('auth')

		api_key = auth._get_apikey_from_request()
		if not api_key:
			abort(401, description='Missing API key')

		key_data = auth.verify_apikey(api_key)
		if not key_data:
			abort(401, description='Invalid or expired API key')

		if key_data.level < 1:
			abort(403, description='Admin privileges required')

		return True

	def require_auth(self, *args: Any, **kwargs: Any) -> bool:
		"""
		Condition function that checks if the current request is authenticated
		via either user JWT token or API key.
		Calls abort(401) if authentication fails.

		Usage:
			@cond(auth.require_auth)
			def protected_route():
				return jsonify({'message': 'Protected content'})

		Aborts with 401 if neither authentication method is valid.
		Returns True if authenticated via either method.
		"""
		assert hasattr(self, 'manager') and isinstance(self.manager, Manager)

		auth = self.manager.get[Plugin]('auth')

		# Try user authentication first
		token = auth._get_token_from_request()
		if token:
			user_data = auth.verify_token(token)
			if user_data:
				return True

		# Try API key authentication
		api_key = auth._get_apikey_from_request()
		if api_key:
			key_data = auth.verify_apikey(api_key)
			if key_data:
				return True

		# Neither authentication method worked
		abort(401, description='Missing or invalid authentication')

	def require_admin(self, *args: Any, **kwargs: Any) -> bool:
		"""
		Condition function that checks if the current request is authenticated
		via either user JWT token or API key, and has admin privileges (level >= 1).
		Calls abort(401) if not authenticated or abort(403) if not admin.

		Usage:
			@cond(auth.require_admin)
			def admin_route():
				return jsonify({'message': 'Admin content'})

		Aborts with 401 if neither authentication method is valid.
		Aborts with 403 if authenticated but not an admin.
		Returns True if authenticated and admin via either method.
		"""
		assert hasattr(self, 'manager') and isinstance(self.manager, Manager)

		auth = self.manager.get[Plugin]('auth')

		# Try user authentication first
		token = auth._get_token_from_request()
		if token:
			user_data = auth.verify_token(token)
			if user_data:
				if user_data.level < 1:
					abort(403, description='Admin privileges required')
				return True

		# Try API key authentication
		api_key = auth._get_apikey_from_request()
		if api_key:
			key_data = auth.verify_apikey(api_key)
			if key_data:
				if key_data.level < 1:
					abort(403, description='Admin privileges required')
				return True

		# Neither authentication method worked
		abort(401, description='Missing or invalid authentication')


class Plugin(ABCPlugin):
	@dataclass
	class UserInfo:
		"""User information without sensitive data."""
		id: int
		username: str
		email: str
		level: int
		created_at: str
		last_login: str | None

	@dataclass
	class TokenPayload:
		"""Decoded JWT token payload."""
		id: int
		username: str
		email: str
		level: int

	@dataclass
	class RegistrationSuccess:
		"""Successful user registration."""
		user_id: int
		username: str

	@dataclass
	class RegistrationError:
		"""Failed user registration."""
		error: str

	RegistrationResult = RegistrationSuccess | RegistrationError

	@dataclass
	class AuthenticationSuccess:
		"""Successful authentication."""
		token: str
		user: "Plugin.UserInfo"

	@dataclass
	class AuthenticationError:
		"""Failed authentication."""
		error: str

	AuthenticationResult = AuthenticationSuccess | AuthenticationError

	@dataclass
	class OperationSuccess:
		"""Successful operation."""
		pass

	@dataclass
	class OperationError:
		"""Failed operation."""
		error: str

	OperationResult = OperationSuccess | OperationError

	def __init__(self, manager: Manager[ABCPlugin]):
		self.manager = manager
		self.user_model = manager.get[User]('models.users')
		self.apikey_model = manager.get[ApiKey]('models.apikeys')
		self.settings = manager.get[Settings]('services.settings')

		# Get JWT secret from settings or generate one
		self.jwt_secret = self.settings.r.jwt_secret or secrets.token_hex(32)
		self.jwt_algorithm = "HS256"
		self.token_expiry_hours = 24

	@property
	def name(self) -> str:
		return "auth"

	def register_user(self, username: str, email: str, password: str, level: int = 0) -> RegistrationResult:
		"""Register a new user."""
		# Validate password strength
		if len(password) < 8:
			return Plugin.RegistrationError(error="Password must be at least 8 characters")

		# Check if username or email already exists
		if self.user_model.username_exists(username):
			return Plugin.RegistrationError(error="Username already exists")

		if self.user_model.email_exists(email):
			return Plugin.RegistrationError(error="Email already exists")

		# Hash password
		password_hash = self.hash_password(password)

		try:
			user_id = self.user_model.create(username, email, password_hash, level)
			return Plugin.RegistrationSuccess(user_id=user_id, username=username)
		except Exception as e:
			return Plugin.RegistrationError(error="Registration failed")

	def authenticate_user(self, username: str, password: str) -> AuthenticationResult:
		"""Authenticate a user and return token."""
		user_record = self.user_model.get_by_username(username)

		if not user_record:
			return Plugin.AuthenticationError(error="Invalid credentials")

		# Verify password
		if not self.verify_password(password, user_record.password_hash):
			return Plugin.AuthenticationError(error="Invalid credentials")

		# Update last login
		self.user_model.update_last_login(user_record.id)

		# Generate JWT token
		token = self.generate_token(user_record.id, user_record.username, user_record.email, user_record.level)

		user_info = Plugin.UserInfo(
			id=user_record.id,
			username=user_record.username,
			email=user_record.email,
			level=user_record.level,
			created_at=user_record.created_at,
			last_login=user_record.last_login
		)

		return Plugin.AuthenticationSuccess(token=token, user=user_info)

	def change_password(self, user_id: int, old_password: str, new_password: str) -> OperationResult:
		"""Change user password."""
		if len(new_password) < 8:
			return Plugin.OperationError(error="Password must be at least 8 characters")

		# Verify old password
		user_record = self.user_model.get_by_id(user_id)
		if not user_record:
			return Plugin.OperationError(error="User not found")

		if not self.verify_password(old_password, user_record.password_hash):
			return Plugin.OperationError(error="Invalid old password")

		# Hash new password
		new_hash = self.hash_password(new_password)
		self.user_model.update(user_id, password_hash=new_hash)

		return Plugin.OperationSuccess()

	def delete_user(self, user_id: int) -> OperationResult:
		"""Delete a user."""
		try:
			if self.user_model.delete(user_id):
				return Plugin.OperationSuccess()
			return Plugin.OperationError(error="User not found")
		except Exception as e:
			return Plugin.OperationError(error=str(e))

	def update_user(self, user_id: int, email: Optional[str] = None, username: Optional[str] = None, level: Optional[int] = None) -> OperationResult:
		"""Update user information."""
		kwargs = {}
		if email:
			kwargs['email'] = email
		if username:
			kwargs['username'] = username
		if level is not None:
			kwargs['level'] = level

		if not kwargs:
			return Plugin.OperationError(error="No fields to update")

		try:
			if self.user_model.update(user_id, **kwargs):
				return Plugin.OperationSuccess()
			return Plugin.OperationError(error="User not found")
		except Exception as e:
			if "UNIQUE constraint failed" in str(e):
				return Plugin.OperationError(error="Username or email already exists")
			return Plugin.OperationError(error=str(e))

	def list_users(self, limit: int = 100, offset: int = 0) -> list[UserInfo]:
		"""Get list of users."""
		user_records = self.user_model.list_users(limit, offset)
		return [
			Plugin.UserInfo(
				id=user.id,
				username=user.username,
				email=user.email,
				level=user.level,
				created_at=user.created_at,
				last_login=user.last_login
			)
			for user in user_records
		]

	def _get_token_from_request(self) -> str | None:
		"""Extract JWT token from request Authorization header."""
		auth_header = request.headers.get('Authorization')
		if not auth_header:
			return None

		# Expected format: "Bearer <token>"
		parts = auth_header.split()
		if len(parts) != 2 or parts[0].lower() != 'bearer':
			return None

		return parts[1]

	def _get_apikey_from_request(self) -> str | None:
		"""Extract API key from request header or query parameter."""
		# Try X-API-Key header first
		api_key = request.headers.get('X-API-Key')
		if api_key:
			return api_key

		# Fall back to query parameter
		api_key = request.args.get('api_key')
		if api_key:
			return api_key

		return None

	def generate_token(self, user_id: int, username: str, email: str, level: int) -> str:
		"""Generate JWT token for user."""
		payload = {
			"user_id": user_id,
			"username": username,
			"email": email,
			"level": level,
			"exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=self.token_expiry_hours),
			"iat": datetime.datetime.now(datetime.timezone.utc),
		}

		return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

	def verify_token(self, token: str) -> TokenPayload | None:
		"""Verify JWT token and return user data."""
		try:
			payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
			return Plugin.TokenPayload(
				id=payload["user_id"],
				username=payload["username"],
				email=payload["email"],
				level=payload.get("level", 0)  # Default to 0 for old tokens
			)
		except jwt.ExpiredSignatureError:
			return None
		except jwt.InvalidTokenError:
			return None

	def verify_apikey(self, api_key: str) -> ApiKeyRecord | None:
		"""Verify API key and return key data if valid."""
		key_record = self.apikey_model.get_by_key(api_key)
		if not key_record:
			return None

		# Check if key is expired
		if self.apikey_model.is_expired(key_record):
			return None

		# Update last used timestamp
		self.apikey_model.update_last_used(key_record.id)

		return key_record

	def hash_password(self, password: str) -> str:
		"""Hash a password using bcrypt."""
		return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

	def verify_password(self, password: str, password_hash: str) -> bool:
		"""Verify a password against its hash."""
		return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

	def get_user_by_username(self, username: str) -> UserInfo | None:
		"""Get user by username."""
		user_record = self.user_model.get_by_username(username)
		if not user_record:
			return None

		return Plugin.UserInfo(
			id=user_record.id,
			username=user_record.username,
			email=user_record.email,
			level=user_record.level,
			created_at=user_record.created_at,
			last_login=user_record.last_login
		)

	def get_user_by_id(self, user_id: int) -> UserInfo | None:
		"""Get user by ID."""
		user_record = self.user_model.get_by_id(user_id)
		if not user_record:
			return None

		return Plugin.UserInfo(
			id=user_record.id,
			username=user_record.username,
			email=user_record.email,
			level=user_record.level,
			created_at=user_record.created_at,
			last_login=user_record.last_login
		)

	def create_apikey(self, level: int = 0, expire: str | None = None) -> str:
		"""Generate and create a new API key."""
		# Generate a secure random API key
		api_key = secrets.token_urlsafe(32)

		# Create the API key in the database
		self.apikey_model.create(api_key, level, expire)

		return api_key

	def list_apikeys(self, limit: int = 100, offset: int = 0) -> list[ApiKeyRecord]:
		"""Get list of API keys."""
		return self.apikey_model.list_apikeys(limit, offset)

	def delete_apikey(self, key_id: int) -> OperationResult:
		"""Delete an API key."""
		try:
			if self.apikey_model.delete(key_id):
				return Plugin.OperationSuccess()
			return Plugin.OperationError(error="API key not found")
		except Exception as e:
			return Plugin.OperationError(error=str(e))

	def get_apikey_by_id(self, key_id: int) -> ApiKeyRecord | None:
		"""Get API key by ID."""
		return self.apikey_model.get_by_id(key_id)

	def get_active_apikeys(self, level: int | None = None) -> list[ApiKeyRecord]:
		"""Get all non-expired API keys, optionally filtered by level."""
		return self.apikey_model.get_active_keys(level)


def setup(manager: Manager[ABCPlugin], /):
	return Plugin(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)
