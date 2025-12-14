from abc import ABC, abstractmethod
from flask import Blueprint, request, current_app, abort
from functools import wraps
from typing import Callable, Any, Literal
import re


class Metadata:
	def __init__(self, func: Callable):
		self._func = func

	def __getattr__(self, key):
		if key in ['_func', 'is_metadata', 'all']: return super().__getattribute__(key)
		try:
			return self[key]
		except: raise AttributeError(key)
	def __setattr__(self, key, value):
		if key in ['_func', 'is_metadata', 'all']: return super().__setattr__(key, value)
		try:
			self[key] = value
		except: raise AttributeError(key, value)
	def __getitem__(self, key): return getattr(self._func, f"_metadata_{key}")
	def __setitem__(self, key, value): setattr(self._func, f"_metadata_{key}", value)

	def is_metadata(self, key: str):
		return key.startswith("_metadata_") and hasattr(self._func, key)

	@property
	def all(self):
		return {k[10:]: self[k[10:]] for k in filter(lambda x: self.is_metadata(x), dir(self._func))}

def cond(functor: Callable):
	def decorator(func):
		@wraps(func)
		def wrapper(*args, **kwargs):
			if functor(*args, **kwargs):
				return func(*args, **kwargs)
			abort(500)

		meta = Metadata(wrapper)
		for k, v in Metadata(func).all.items(): meta[k] = v

		return wrapper
	return decorator

def describe(
	description: str,
	type: Literal["route"] | Literal["specs"] = "route",
	*,
	params: dict[str, dict] | None = None,
	method: str = "GET",
	documentation: str = ""
) -> Callable:
	"""
	Decorator to add documentation to an endpoint.

	Usage:
		@describe(
			"Returns user information",
			params={
				"user_id": {
					"type": "string",
					"required": True,
					"description": "The user ID",
					"in": "path"
				},
				"include_posts": {
					"type": "boolean",
					"required": False,
					"description": "Include user posts",
					"in": "query"
				}
			},
			method="GET"
		)
		def get_user(self):
			'''Detailed docstring about the endpoint'''
			return {"user": "data"}
	"""
	def decorator(func: Callable) -> Callable:
		@wraps(func)
		def wrapper(*args, **kwargs):
			return func(*args, **kwargs)

		meta = Metadata(wrapper)
		for k, v in Metadata(func).all.items(): meta[k] = v

		meta.describe_text = description
		meta.describe_doc = func.__doc__
		meta.describe_params = params or {}
		meta.describe_method = method
		meta.describe_type = type
		meta.describe_documentation = documentation

		return wrapper
	return decorator


def register(url: str, *args, **kwargs):
	"""
	Decorator to add metadata to automatically register the function as a flask view function.

	Usage:
		@register(
			"/index",
			method="GET"
		)
		def index(self):
			return {"index": "hello"}
	"""
	def decorator(func: Callable) -> Callable:
		@wraps(func)
		def wrapper(*a, **kw):
			return func(*a, **kw)

		meta = Metadata(wrapper)
		for k, v in Metadata(func).all.items(): meta[k] = v

		meta.register_url = url
		meta.register_args = args
		meta.register_kwargs = kwargs

		return wrapper
	return decorator


class ABCApi(ABC):
	@property
	@abstractmethod
	def name(self) -> str: ...

	@property
	@abstractmethod
	def blueprint(self) -> Blueprint: ...

	def add_rules(self, bp: Blueprint) -> None:
		for attr_name in dir(self):
			if attr_name.startswith('_'):
				continue
			attr = getattr(self, attr_name)
			metadata = Metadata(attr)
			if not hasattr(metadata, 'register_url'):
				continue
			url = metadata.register_url
			args = metadata.register_args
			kwargs = metadata.register_kwargs

			bp.add_url_rule(url, *args, **(kwargs | {'view_func': attr}))

	def _build_describe_response(self, func_name: str | None) -> dict | tuple[dict, int]:
		"""Build the response for the /describe endpoint."""
		if func_name:
			# Return description for specific function
			if not hasattr(self, func_name):
				return {"error": f"Function '{func_name}' not found"}, 404

			method = getattr(self, func_name)
			metadata = Metadata(method)

			if not hasattr(metadata, 'describe_text'):
				return {"error": f"Function '{func_name}' has no description"}, 404

			# Build full endpoint path by walking up parent chain
			endpoint_parts = [self.blueprint.name, func_name]
			current = self
			while hasattr(current, '_parent_api') and current._parent_api is not None:
				current = current._parent_api
				endpoint_parts.insert(0, current.blueprint.name)

			expected_endpoint = '.'.join(endpoint_parts)

			# Find route with exact endpoint match
			route = None
			for rule in current_app.url_map.iter_rules():
				if rule.endpoint == expected_endpoint:
					route = re.sub(r'<(?:\w+:)?(\w+)>', r'{\1}', rule.rule)
					break

			return {
				"function": func_name,
				"description": metadata.describe_text,
				"docstring": metadata.describe_doc,
				"route": route,
				"params": getattr(metadata, 'describe_params', {}),
				"method": getattr(metadata, 'describe_method', 'GET'),
				"type": getattr(metadata, 'describe_type', 'route'),
				"documentation": getattr(metadata, 'describe_documentation', '')
			}
		else:
			# List all describable functions
			describable = []
			for attr_name in dir(self):
				if attr_name.startswith('_'):
					continue
				attr = getattr(self, attr_name)
				metadata = Metadata(attr)

				if not hasattr(metadata, 'describe_text'):
					continue

				# Build full endpoint path by walking up parent chain
				endpoint_parts = [self.blueprint.name, attr_name]
				current = self
				while hasattr(current, '_parent_api') and current._parent_api is not None:
					current = current._parent_api
					endpoint_parts.insert(0, current.blueprint.name)

				expected_endpoint = '.'.join(endpoint_parts)

				# Find route with exact endpoint match
				route = None
				for rule in current_app.url_map.iter_rules():
					if rule.endpoint == expected_endpoint:
						route = re.sub(r'<(?:\w+:)?(\w+)>', r'{\1}', rule.rule)
						break

				describable.append({
					"function": attr_name,
					"description": metadata.describe_text,
					"docstring": metadata.describe_doc,
					"route": route,
					"params": getattr(metadata, 'describe_params', {}),
					"method": getattr(metadata, 'describe_method', 'GET'),
					"type": getattr(metadata, 'describe_type', 'route'),
					"documentation": getattr(metadata, 'describe_documentation', ''),
					"_index": getattr(metadata, 'index', len(describable)),
				})
			return {"functions": sorted(describable, key=lambda x: x['_index'])}


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
		# Store parent reference for endpoint path resolution
		self._parent_api = parent

		if import_name is None:
			import_name = self.__class__.__module__
		bp = Blueprint(name, import_name, *args, **kwargs)

		# Automatically add /describe endpoint
		def describe_endpoint():
			func_name = request.args.get('f')
			return self._build_describe_response(func_name)

		bp.add_url_rule('/describe', 'describe', describe_endpoint)

		if parent is not None:
			parent.blueprint.register_blueprint(bp)
		return bp
