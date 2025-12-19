from abc import ABC, abstractmethod


class ABCService(ABC):
	@property
	@abstractmethod
	def name(self) -> str: ...

	@property
	@abstractmethod
	def ready(self) -> bool: ...
