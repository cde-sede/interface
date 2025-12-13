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

class AuthUtils:
	manager: Manager
	def require_auth(self, *args: Any, **kwargs: Any) -> bool:
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


class Plugin(ABCPlugin):
	@dataclass
	class UserInfo:
		"""User information without sensitive data."""
		id: int
		username: str
		email: str
		created_at: str
		last_login: str | None

	@dataclass
	class TokenPayload:
		"""Decoded JWT token payload."""
		id: int
		username: str
		email: str

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
		self.db = manager.get[DB]('services.db')
		self.settings = manager.get[Settings]('services.settings')

		# Get JWT secret from settings or generate one
		self.jwt_secret = self.settings.r.jwt_secret or secrets.token_hex(32)
		self.jwt_algorithm = "HS256"
		self.token_expiry_hours = 24

		self._init_database()

	def _init_database(self):
		"""Initialize users table if it doesn't exist."""
		with self.db() as cursor:
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS users (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					username TEXT UNIQUE NOT NULL,
					email TEXT UNIQUE NOT NULL,
					password_hash TEXT NOT NULL,
					created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
					last_login TIMESTAMP
				)
			""")

			cursor.execute("""
				CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)
			""")

			cursor.execute("""
				CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
			""")

	@property
	def name(self) -> str:
		return "auth"

	def register_user(self, username: str, email: str, password: str) -> RegistrationResult:
		"""Register a new user."""
		# Validate password strength
		if len(password) < 8:
			return Plugin.RegistrationError(error="Password must be at least 8 characters")

		# Hash password
		password_hash = self.hash_password(password)

		try:
			with self.db() as cursor:
				cursor.execute(
					"INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
					(username, email, password_hash)
				)
				user_id = cursor.lastrowid

			assert user_id is not None
			return Plugin.RegistrationSuccess(user_id=user_id, username=username)

		except Exception as e:
			if "UNIQUE constraint failed" in str(e):
				return Plugin.RegistrationError(error="Username or email already exists")
			return Plugin.RegistrationError(error="Registration failed")

	def authenticate_user(self, username: str, password: str) -> AuthenticationResult:
		"""Authenticate a user and return token."""
		with self.db() as cursor:
			cursor.execute(
				"SELECT id, username, email, password_hash, created_at, last_login FROM users WHERE username = ?",
				(username,)
			)
			user = cursor.fetchone()

		if not user:
			return Plugin.AuthenticationError(error="Invalid credentials")

		user_id, username, email, password_hash, created_at, last_login = user

		# Verify password
		if not self.verify_password(password, password_hash):
			return Plugin.AuthenticationError(error="Invalid credentials")

		# Update last login
		with self.db() as cursor:
			cursor.execute(
				"UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
				(user_id,)
			)

		# Generate JWT token
		token = self.generate_token(user_id, username, email)

		user_info = Plugin.UserInfo(
			id=user_id,
			username=username,
			email=email,
			created_at=created_at,
			last_login=last_login
		)

		return Plugin.AuthenticationSuccess(token=token, user=user_info)

	def change_password(self, user_id: int, old_password: str, new_password: str) -> OperationResult:
		"""Change user password."""
		if len(new_password) < 8:
			return Plugin.OperationError(error="Password must be at least 8 characters")

		# Verify old password
		with self.db() as cursor:
			cursor.execute(
				"SELECT password_hash FROM users WHERE id = ?",
				(user_id,)
			)
			result = cursor.fetchone()

		if not result:
			return Plugin.OperationError(error="User not found")

		password_hash = result[0]

		if not self.verify_password(old_password, password_hash):
			return Plugin.OperationError(error="Invalid old password")

		# Hash new password
		new_hash = self.hash_password(new_password)

		with self.db() as cursor:
			cursor.execute(
				"UPDATE users SET password_hash = ? WHERE id = ?",
				(new_hash, user_id)
			)

		return Plugin.OperationSuccess()

	def delete_user(self, user_id: int) -> OperationResult:
		"""Delete a user."""
		try:
			with self.db() as cursor:
				cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
				if cursor.rowcount == 0:
					return Plugin.OperationError(error="User not found")

			return Plugin.OperationSuccess()
		except Exception as e:
			return Plugin.OperationError(error=str(e))

	def update_user(self, user_id: int, email: Optional[str] = None, username: Optional[str] = None) -> OperationResult:
		"""Update user information."""
		updates = []
		params = []

		if email:
			updates.append("email = ?")
			params.append(email)

		if username:
			updates.append("username = ?")
			params.append(username)

		if not updates:
			return Plugin.OperationError(error="No fields to update")

		params.append(user_id)

		try:
			with self.db() as cursor:
				cursor.execute(
					f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
					params
				)
				if cursor.rowcount == 0:
					return Plugin.OperationError(error="User not found")

			return Plugin.OperationSuccess()
		except Exception as e:
			if "UNIQUE constraint failed" in str(e):
				return Plugin.OperationError(error="Username or email already exists")
			return Plugin.OperationError(error=str(e))

	def list_users(self, limit: int = 100, offset: int = 0) -> list[UserInfo]:
		"""Get list of users."""
		with self.db() as cursor:
			cursor.execute(
				"SELECT id, username, email, created_at, last_login FROM users LIMIT ? OFFSET ?",
				(limit, offset)
			)
			users = cursor.fetchall()

		return [
			Plugin.UserInfo(
				id=user[0],
				username=user[1],
				email=user[2],
				created_at=user[3],
				last_login=user[4]
			)
			for user in users
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

	def generate_token(self, user_id: int, username: str, email: str) -> str:
		"""Generate JWT token for user."""
		payload = {
			"user_id": user_id,
			"username": username,
			"email": email,
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
				email=payload["email"]
			)
		except jwt.ExpiredSignatureError:
			return None
		except jwt.InvalidTokenError:
			return None

	def hash_password(self, password: str) -> str:
		"""Hash a password using bcrypt."""
		return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

	def verify_password(self, password: str, password_hash: str) -> bool:
		"""Verify a password against its hash."""
		return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

	def get_user_by_username(self, username: str) -> UserInfo | None:
		"""Get user by username."""
		with self.db() as cursor:
			cursor.execute(
				"SELECT id, username, email, created_at, last_login FROM users WHERE username = ?",
				(username,)
			)
			user = cursor.fetchone()

		if not user:
			return None

		return Plugin.UserInfo(
			id=user[0],
			username=user[1],
			email=user[2],
			created_at=user[3],
			last_login=user[4]
		)

	def get_user_by_id(self, user_id: int) -> UserInfo | None:
		"""Get user by ID."""
		with self.db() as cursor:
			cursor.execute(
				"SELECT id, username, email, created_at, last_login FROM users WHERE id = ?",
				(user_id,)
			)
			user = cursor.fetchone()

		if not user:
			return None

		return Plugin.UserInfo(
			id=user[0],
			username=user[1],
			email=user[2],
			created_at=user[3],
			last_login=user[4]
		)


def setup(manager: Manager[ABCPlugin], /):
	return Plugin(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)
