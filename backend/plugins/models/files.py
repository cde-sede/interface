from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from _injected import *

from enum import IntEnum, auto
from ._model import ABCModel
from .._base_plugin import ABCPlugin
from .._manager import Manager

class SENTINEL:
	def __eq__(self, *a): return False
	def __lt__(self, *a): return False
	def __le__(self, *a): return False
	def __gt__(self, *a): return False
	def __ge__(self, *a): return False
	def __bool__(self, *a): return False

_SENTINEL = SENTINEL()

class File(ABCModel):
	class FileTypes(IntEnum):
		STATIC = auto()
		DOWNLOADER = auto()
		
	def __init__(self, manager):
		super().__init__(manager)

	@property
	def name(self) -> str:
		return "files"

	def ensure(self):
		# `type` being the "origin" of the file
		# for example it could be from a plugin, a static, anything
		with self.db() as db:
			return db.execute("CREATE TABLE IF NOT EXISTS files (id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL, type TINYINT);").fetchall()

	def create(self, path: str, type: FileTypes):
		with self.db() as db:
			return db.execute("INSERT INTO files (path, type) VALUES (?, ?)", (str(path), int(type))).fetchall()

	def delete(self, id: int) -> bool:
		"""
		Delete a file record.

		Args:
			id: File ID to delete

		Returns:
			bool: True if deletion was successful, False otherwise
		"""
		with self.db() as db:
			db.execute("DELETE FROM files WHERE id = ?", (id,))
			return db.rowcount > 0

	def update(self, id: int, *, path: str | SENTINEL=_SENTINEL, type: int | SENTINEL=_SENTINEL):
		with self.db() as db:
			if path is not _SENTINEL and type is not _SENTINEL:
				return db.execute("UPDATE files SET path=(?), type=(?) where id=(?)", (path, type, id)).fetchall()
			elif path is not _SENTINEL:
				return db.execute("UPDATE files SET path=(?) where id=(?)", (path, id)).fetchall()
			elif type is not _SENTINEL:
				return db.execute("UPDATE files SET type=(?) where id=(?)", (type, id)).fetchall()
			raise ValueError("Need at least one from `path` and `type`")

	def get_all(self, limit: int = 50, offset: int = 0) -> list[dict]:
		"""Get all files with pagination"""
		with self.db() as db:
			cursor = db.execute(
				"SELECT id, path, type FROM files ORDER BY id DESC LIMIT ? OFFSET ?",
				(limit, offset)
			)
			rows = cursor.fetchall()

		return [
			{
				'id': row[0],
				'path': row[1],
				'type': row[2]
			}
			for row in rows
		]

	def get_count(self) -> int:
		"""Get total count of files"""
		with self.db() as db:
			cursor = db.execute("SELECT COUNT(*) FROM files")
			result = cursor.fetchone()
			return result[0] if result else 0

	def get_column_definitions(self) -> list[dict]:
		"""Get column definitions for admin UI"""
		return [
			{"key": "id", "label": "ID", "type": "number", "sortable": True, "truncate": False},
			{"key": "path", "label": "Path", "type": "text", "sortable": True, "truncate": True},
			{"key": "type", "label": "Type", "type": "number", "sortable": True, "truncate": False},
		]

def setup(manager: Manager[ABCPlugin], /):
	return File(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)

