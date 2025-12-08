from abc import ABC, abstractmethod
from flask import Blueprint

class ABCPlugin(ABC):
	@property
	@abstractmethod
	def name(self) -> str: ...

	@property
	@abstractmethod
	def blueprint(self) -> Blueprint: ...

	def create_blueprint(self, name: str, *args, parent: 'ABCPlugin | None' = None, import_name: str | None = None, **kwargs) -> Blueprint:
		"""
		Create a Flask Blueprint, optionally registering it with a parent.

		Args:
			name: Blueprint name
			*args: Positional arguments forwarded to Blueprint()
			parent: Optional parent plugin to register this blueprint with
			import_name: Optional import name for the blueprint (defaults to the module where the class is defined)
			**kwargs: Keyword arguments forwarded to Blueprint()

		Returns:
			The created Blueprint instance
		"""
		if import_name is None:
			import_name = self.__class__.__module__
		bp = Blueprint(name, import_name, *args, **kwargs)
		if parent is not None:
			parent.blueprint.register_blueprint(bp)
		return bp
