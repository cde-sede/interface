from abc import ABC, abstractmethod
from flask import Blueprint

class ABCService(ABC):
	@property
	@abstractmethod
	def name(self) -> str: ...
