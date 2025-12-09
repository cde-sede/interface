from abc import ABC, abstractmethod
from flask import Blueprint

class ABCPlugin(ABC):
	@property
	@abstractmethod
	def name(self) -> str: ...
