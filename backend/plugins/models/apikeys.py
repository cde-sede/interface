from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
	from ..._injected import validate_setup

from ._model import ABCModel
from .._manager import Manager, ABCPlugin
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ApiKeyRecord:
	"""API Key database record."""
	id: int
	key: str
	expire: str | None
	created_at: str
	last_used: str | None
	level: int

class ApiKey(ABCModel):
	"""API Key model for authentication and authorization."""

	@property
	def name(self) -> str:
		return "apikeys"

	def ensure(self):
		"""Ensure apikeys table exists."""
		with self.db() as cursor:
			cursor.execute("""
				CREATE TABLE IF NOT EXISTS apikeys (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					key TEXT UNIQUE NOT NULL,
					expire TIMESTAMP,
					created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
					last_used TIMESTAMP,
					level INTEGER DEFAULT 0
				)
			""")

			cursor.execute("""
				CREATE INDEX IF NOT EXISTS idx_apikeys_key ON apikeys(key)
			""")

			cursor.execute("""
				CREATE INDEX IF NOT EXISTS idx_apikeys_expire ON apikeys(expire)
			""")

	def create(self, key: str, level: int = 0, expire: str | None = None) -> int:
		"""Create a new API key."""
		with self.db() as cursor:
			cursor.execute(
				"INSERT INTO apikeys (key, level, expire) VALUES (?, ?, ?)",
				(key, level, expire)
			)
			return cursor.lastrowid

	def get_by_id(self, key_id: int) -> ApiKeyRecord | None:
		"""Get API key by ID."""
		with self.db() as cursor:
			cursor.execute(
				"SELECT id, key, expire, created_at, last_used, level FROM apikeys WHERE id = ?",
				(key_id,)
			)
			row = cursor.fetchone()

		if not row:
			return None

		return ApiKeyRecord(*row)

	def get_by_key(self, key: str) -> ApiKeyRecord | None:
		"""Get API key by key string."""
		with self.db() as cursor:
			cursor.execute(
				"SELECT id, key, expire, created_at, last_used, level FROM apikeys WHERE key = ?",
				(key,)
			)
			row = cursor.fetchone()

		if not row:
			return None

		return ApiKeyRecord(*row)

	def list_apikeys(self, limit: int = 100, offset: int = 0) -> list[ApiKeyRecord]:
		"""List API keys with pagination."""
		with self.db() as cursor:
			cursor.execute(
				"SELECT id, key, expire, created_at, last_used, level FROM apikeys LIMIT ? OFFSET ?",
				(limit, offset)
			)
			rows = cursor.fetchall()

		return [ApiKeyRecord(*row) for row in rows]

	def update(self, key_id: int, **kwargs) -> bool:
		"""Update API key fields."""
		allowed_fields = {'key', 'level', 'expire', 'last_used'}
		updates = []
		params = []

		for key, value in kwargs.items():
			if key in allowed_fields:
				updates.append(f"{key} = ?")
				params.append(value)

		if not updates:
			return False

		params.append(key_id)

		with self.db() as cursor:
			cursor.execute(
				f"UPDATE apikeys SET {', '.join(updates)} WHERE id = ?",
				params
			)
			return cursor.rowcount > 0

	def delete(self, key_id: int) -> bool:
		"""Delete an API key."""
		with self.db() as cursor:
			cursor.execute("DELETE FROM apikeys WHERE id = ?", (key_id,))
			return cursor.rowcount > 0

	def update_last_used(self, key_id: int):
		"""Update API key's last used timestamp."""
		with self.db() as cursor:
			cursor.execute(
				"UPDATE apikeys SET last_used = CURRENT_TIMESTAMP WHERE id = ?",
				(key_id,)
			)

	def key_exists(self, key: str) -> bool:
		"""Check if API key exists."""
		with self.db() as cursor:
			cursor.execute("SELECT 1 FROM apikeys WHERE key = ? LIMIT 1", (key,))
			return cursor.fetchone() is not None

	def is_expired(self, key_record: ApiKeyRecord) -> bool:
		"""Check if an API key is expired."""
		if key_record.expire is None:
			return False

		try:
			expire_time = datetime.fromisoformat(key_record.expire)
			return datetime.now() > expire_time
		except (ValueError, TypeError):
			return False

	def get_active_keys(self, level: int | None = None) -> list[ApiKeyRecord]:
		"""Get all non-expired API keys, optionally filtered by level."""
		with self.db() as cursor:
			if level is not None:
				cursor.execute(
					"""SELECT id, key, expire, created_at, last_used, level
					FROM apikeys
					WHERE (expire IS NULL OR expire > CURRENT_TIMESTAMP) AND level = ?""",
					(level,)
				)
			else:
				cursor.execute(
					"""SELECT id, key, expire, created_at, last_used, level
					FROM apikeys
					WHERE expire IS NULL OR expire > CURRENT_TIMESTAMP"""
				)
			rows = cursor.fetchall()

		return [ApiKeyRecord(*row) for row in rows]

	def get_all(self, limit: int = 50, offset: int = 0) -> list[dict]:
		"""Get all API keys with pagination"""
		with self.db() as cursor:
			cursor.execute(
				"SELECT id, key, expire, created_at, last_used, level FROM apikeys ORDER BY created_at DESC LIMIT ? OFFSET ?",
				(limit, offset)
			)
			rows = cursor.fetchall()

		return [
			{
				'id': row[0],
				'key': row[1],
				'expire': row[2],
				'created_at': row[3],
				'last_used': row[4],
				'level': row[5]
			}
			for row in rows
		]

	def get_count(self) -> int:
		"""Get total count of API keys"""
		with self.db() as cursor:
			cursor.execute("SELECT COUNT(*) FROM apikeys")
			result = cursor.fetchone()
			return result[0] if result else 0

	def get_column_definitions(self) -> list[dict]:
		"""Get column definitions for admin UI"""
		return [
			{"key": "id", "label": "ID", "type": "number", "sortable": True, "truncate": False},
			{"key": "key", "label": "Key", "type": "code", "sortable": False, "truncate": True},
			{"key": "level", "label": "Level", "type": "number", "sortable": True, "truncate": False},
			{"key": "expire", "label": "Expires", "type": "date", "sortable": True, "truncate": False},
			{"key": "created_at", "label": "Created", "type": "date", "sortable": True, "truncate": False},
			{"key": "last_used", "label": "Last Used", "type": "date", "sortable": True, "truncate": False},
		]


def setup(manager: Manager[ABCPlugin], /):
	return ApiKey(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)
