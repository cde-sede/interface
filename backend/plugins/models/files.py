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

	def delete(self, id):
		with self.db() as db:
			return db.execute("DELETE FROM files WHERE id=(?)", (id,)).fetchall()

	def update(self, id: int, *, path: str | SENTINEL=_SENTINEL, type: int | SENTINEL=_SENTINEL):
		with self.db() as db:
			if path is not _SENTINEL and type is not _SENTINEL:
				return db.execute("UPDATE files SET path=(?), type=(?) where id=(?)", (path, type, id)).fetchall()
			elif path is not _SENTINEL:
				return db.execute("UPDATE files SET path=(?) where id=(?)", (path, id)).fetchall()
			elif type is not _SENTINEL:
				return db.execute("UPDATE files SET type=(?) where id=(?)", (type, id)).fetchall()
			raise ValueError("Need at least one from `path` and `type`")

def setup(manager: Manager[ABCPlugin], /):
	return File(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)

