from abc import ABC, abstractmethod
from flask import Blueprint
from functools import wraps
from typing import Callable


def describe(description: str) -> Callable:
	"""
	Decorator to add documentation to an endpoint.

	Usage:
		@describe("Returns user information")
		def get_user(self):
			'''Detailed docstring about the endpoint'''
			return {"user": "data"}
	"""
	def decorator(func: Callable) -> Callable:
		@wraps(func)
		def wrapper(*args, **kwargs):
			return func(*args, **kwargs)

		# Store metadata on the function
		wrapper._describe_text = description  # type: ignore
		wrapper._describe_doc = func.__doc__  # type: ignore
		return wrapper

	return decorator


class ABCApi(ABC):
	@property
	@abstractmethod
	def name(self) -> str: ...

	@property
	@abstractmethod
	def blueprint(self) -> Blueprint: ...

	def create_blueprint(self, name: str, *args, parent: 'ABCApi | None' = None, import_name: str | None = None, **kwargs) -> Blueprint:
		"""
		Create a Flask Blueprint, optionally registering it with a parent.

		Args:
			name: Blueprint name
			*args: Positional arguments forwarded to Blueprint()
			parent: Optional parent API to register this blueprint with
			import_name: Optional import name for the blueprint (defaults to the module where the class is defined)
			**kwargs: Keyword arguments forwarded to Blueprint()

		Returns:
			The created Blueprint instance
		"""
		if import_name is None:
			import_name = self.__class__.__module__
		bp = Blueprint(name, import_name, *args, **kwargs)

		# Automatically add /describe endpoint
		def describe_endpoint():
			from flask import request, current_app
			func_name = request.args.get('f')

			if func_name:
				# Return description for specific function
				if hasattr(self, func_name):
					method = getattr(self, func_name)
					if hasattr(method, '_describe_text'):
						# Find the route for this function
						route = None
						for rule in current_app.url_map.iter_rules():
							if rule.endpoint.endswith(f'.{func_name}'):
								route = rule.rule
								break

						return {
							"function": func_name,
							"description": method._describe_text,
							"docstring": method._describe_doc,
							"route": route
						}
					else:
						return {"error": f"Function '{func_name}' has no description"}, 404
				else:
					return {"error": f"Function '{func_name}' not found"}, 404
			else:
				# List all describable functions
				from flask import current_app
				describable = []
				for attr_name in dir(self):
					if attr_name.startswith('_'):
						continue
					attr = getattr(self, attr_name)
					if hasattr(attr, '_describe_text'):
						# Find the route for this function
						route = None
						for rule in current_app.url_map.iter_rules():
							if rule.endpoint.endswith(f'.{attr_name}'):
								route = rule.rule
								break

						describable.append({
							"function": attr_name,
							"description": attr._describe_text,
							"docstring": attr._describe_doc,
							"route": route
						})
				return {"functions": describable}

		bp.add_url_rule('/describe', 'describe', describe_endpoint)

		if parent is not None:
			parent.blueprint.register_blueprint(bp)
		return bp
