from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from ._base_service import ABCService
from ._manager import Manager
from .migrations import Service as Migrations
from .settings import Service as Settings
import sqlite3


class _DB:
	def __init__(self, path):
		self.path = path

	def __enter__(self) -> sqlite3.Cursor:
		self._db = sqlite3.connect(self.path)
		self.cursor = self._db.cursor()
		return self.cursor

	def __exit__(self, exc_type, exc_val, exc_tb):
		if exc_type:
			self._db.rollback()
			return
		self._db.commit()


class Service(ABCService):
	def __init__(self, manager: Manager[ABCService]):
		self.manager = manager

		self.settings: Settings = cast(Settings, self.manager.get('settings'))
		self.migrations: Migrations = cast(Migrations, self.manager.get('migrations'))

	def __call__(self):
		return _DB(self.settings.db)

	@property
	def name(self) -> str:
		return "db"

	@property
	def ready(self) -> bool:
		return True

#	def query(self, sql: str):
#		connection = self.connection
#		data = connection.execute(sql).fetchall()
#		connection.commit()
#		return data

def setup(manager: Manager[ABCService], /):
	require("settings")
	require("cache")
	require("migrations")
	return Service(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)
