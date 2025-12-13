from typing import Any
from abc import ABC, abstractmethod
from .._base_plugin import ABCPlugin
from .._manager import Manager
from ...services.db import Service as DB

class ABCModel(ABCPlugin, ABC):
	def __init__(self, manager: Manager[ABCPlugin]):
		self._db = manager.get[DB]('services.db')
		self.ensure()

	@property
	def db(self) -> DB:
		return self._db

	@abstractmethod
	def ensure(self, *args, **kwargs) -> Any: ...
	@abstractmethod
	def create(self, *args, **kwargs) -> Any: ...
	@abstractmethod
	def delete(self, *args, **kwargs) -> Any: ...
	@abstractmethod
	def update(self, *args, **kwargs) -> Any: ...
