from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
	from ..._injected import validate_setup

from ._model import ABCModel
from .._manager import Manager, ABCPlugin
from dataclasses import dataclass

@dataclass
class UserRecord:
	"""User database record."""
	id: int
	username: str
	email: str
	password_hash: str
	level: int
	created_at: str
	last_login: str | None

class User(ABCModel):
	"""User model for authentication and authorization."""

	@property
	def name(self) -> str:
		return "users"

	def ensure(self):
		"""Ensure users table exists."""
		with self.db() as cursor:
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS users (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					username TEXT UNIQUE NOT NULL,
					email TEXT UNIQUE NOT NULL,
					password_hash TEXT NOT NULL,
					level INTEGER DEFAULT 0,
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

	def create(self, username: str, email: str, password_hash: str, level: int = 0) -> int:
		"""Create a new user."""
		with self.db() as cursor:
			cursor.execute(
				"INSERT INTO users (username, email, password_hash, level) VALUES (?, ?, ?, ?)",
				(username, email, password_hash, level)
			)
			return cursor.lastrowid

	def get_by_id(self, user_id: int) -> UserRecord | None:
		"""Get user by ID."""
		with self.db() as cursor:
			cursor.execute(
				"SELECT id, username, email, password_hash, level, created_at, last_login FROM users WHERE id = ?",
				(user_id,)
			)
			row = cursor.fetchone()

		if not row:
			return None

		return UserRecord(*row)

	def get_by_username(self, username: str) -> UserRecord | None:
		"""Get user by username."""
		with self.db() as cursor:
			cursor.execute(
				"SELECT id, username, email, password_hash, level, created_at, last_login FROM users WHERE username = ?",
				(username,)
			)
			row = cursor.fetchone()

		if not row:
			return None

		return UserRecord(*row)

	def get_by_email(self, email: str) -> UserRecord | None:
		"""Get user by email."""
		with self.db() as cursor:
			cursor.execute(
				"SELECT id, username, email, password_hash, level, created_at, last_login FROM users WHERE email = ?",
				(email,)
			)
			row = cursor.fetchone()

		if not row:
			return None

		return UserRecord(*row)

	def list_users(self, limit: int = 100, offset: int = 0) -> list[UserRecord]:
		"""List users with pagination."""
		with self.db() as cursor:
			cursor.execute(
				"SELECT id, username, email, password_hash, level, created_at, last_login FROM users LIMIT ? OFFSET ?",
				(limit, offset)
			)
			rows = cursor.fetchall()

		return [UserRecord(*row) for row in rows]

	def update(self, user_id: int, **kwargs) -> bool:
		"""Update user fields."""
		allowed_fields = {'username', 'email', 'password_hash', 'level', 'last_login'}
		updates = []
		params = []

		for key, value in kwargs.items():
			if key in allowed_fields:
				updates.append(f"{key} = ?")
				params.append(value)

		if not updates:
			return False

		params.append(user_id)

		with self.db() as cursor:
			cursor.execute(
				f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
				params
			)
			return cursor.rowcount > 0

	def delete(self, user_id: int) -> bool:
		"""Delete a user."""
		with self.db() as cursor:
			cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
			return cursor.rowcount > 0

	def update_last_login(self, user_id: int):
		"""Update user's last login timestamp."""
		with self.db() as cursor:
			cursor.execute(
				"UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
				(user_id,)
			)

	def username_exists(self, username: str) -> bool:
		"""Check if username exists."""
		with self.db() as cursor:
			cursor.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,))
			return cursor.fetchone() is not None

	def email_exists(self, email: str) -> bool:
		"""Check if email exists."""
		with self.db() as cursor:
			cursor.execute("SELECT 1 FROM users WHERE email = ? LIMIT 1", (email,))
			return cursor.fetchone() is not None


def setup(manager: Manager[ABCPlugin], /):
	return User(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)
