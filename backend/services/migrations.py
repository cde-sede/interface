from __future__ import annotations
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup
	from .logs import Service as Logs

from collections.abc import Callable
from ._base_service import ABCService
from ._manager import Manager
from pathlib import Path


#def run_migration(from_, to):
#	run = False
#	for migration in migrations:
#		if migration.version == from_:
#			run = True
#		if migration.version == to:
#			break
#		if run:
#			sql = diff.from_ir(migration.ir)
#			db.query(sql)


	

class Migration:
	def __init__(self, path: str | Path):
		self.path = Path(path)
		self.version = ""
		self.query = ""
		self.revert = ""

		with open(self.path, 'r') as f:
			pass


class Service(ABCService):
	def __init__(self, manager: Manager[ABCService]):
		self.manager = manager
		self._query: Callable | None = None
		self._ready = False
		self._logs: Optional[Logs] = None

	@property
	def query(self):
		return self._query

	@query.setter
	def query(self, other):
		self._query = other

	@property
	def logs(self):
		if self._logs is None or not self._logs.ready:
			from .logs import Service as Logs
			self._logs = self.manager.get[Logs]('logs')
		return self._logs

	@property
	def name(self) -> str:
		return "migrations"

	@property
	def ready(self) -> bool:
		return self._ready

	@ready.setter
	def ready(self, other):
		self._ready = True

	def discover_migrations(self):
		pass

	def run(self, query_function: Callable):
		self.logs.info("Running migrations", service="migrations")
		self.query = query_function
		self.ready = True
		self.logs.info("Migrations completed successfully", service="migrations")
		return True

def setup(manager: Manager[ABCService], /):
	require('logs')
	return Service(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)
