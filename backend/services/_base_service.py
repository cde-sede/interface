from abc import ABC, abstractmethod
from flask import Flask


class ABCService(ABC):
	@property
	@abstractmethod
	def name(self) -> str: ...

	@property
	@abstractmethod
	def ready(self) -> bool: ...

	def initialize(self, app: Flask):
		pass
