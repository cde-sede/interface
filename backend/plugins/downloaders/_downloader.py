from typing import Any
from abc import ABC, abstractmethod
from .._base_plugin import ABCPlugin
from .._manager import Manager

class ABCDownloader(ABCPlugin, ABC):

	@abstractmethod
	def match(self, url: str) -> bool: ...

	@abstractmethod
	def run(self, url: str) -> bool: ...

	@abstractmethod
	def defer(self, url: str) -> bool: ...

