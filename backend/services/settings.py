from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from ._base_service import ABCService
from ._manager import Manager
from .migrations import Service as Migrations
import json
import sqlite3


_SETTINGS = {}
class SENTINEL:
	def __eq__(self, *a): return False
	def __lt__(self, *a): return False
	def __le__(self, *a): return False
	def __gt__(self, *a): return False
	def __ge__(self, *a): return False
	def __bool__(self, *a): return False

_SENTINEL = SENTINEL()

class _SettingsRegistry[U]:
	def __getitem__[T](self, key: type[T]) -> '_SettingsRegistry[T]':
		return cast('_SettingsRegistry[T]', self)

	def __getattr__(self, key) -> U:
		return _SETTINGS.get(key, _SENTINEL)

class Service(ABCService):
	def __init__(self):
		self.r = _SettingsRegistry()
		with open("settings.json", 'r') as f:
			global _SETTINGS
			_SETTINGS = json.load(f)

	@property
	def name(self) -> str:
		return "settings"

	@property
	def ready(self) -> bool:
		return True

	@property
	def db(self) -> str:
		return self.r[str].db or ":memory:"


def setup(manager: Manager[ABCService], /):
	return Service()

if TYPE_CHECKING:
	setup = validate_setup(setup)
