from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from _injected import *

from ._base_api import ABCApi, describe
from ._manager import Manager
from flask import Blueprint, current_app


class API(ABCApi):
	def __init__(self, manager: Manager[ABCApi]):
		self.manager = manager
		self.bp = self.create_blueprint("api", url_prefix="/api")

		self.bp.add_url_rule("/", view_func=self.list_apis)

	@property
	def isroot(self) -> bool:
		return True

	@describe("Lists all registered API modules and their routes")
	def list_apis(self):
		"""Returns a comprehensive list of all loaded API modules with their blueprints and available routes."""

		apis = []
		for module in self.manager.modules:
			bp = module.blueprint
			bp_name = bp.name

			endpoint_prefix_parts = [bp_name]
			current = module
			while hasattr(current, '_parent_api') and current._parent_api is not None:
				current = current._parent_api
				endpoint_prefix_parts.insert(0, current.blueprint.name)

			endpoint_prefix = '.'.join(endpoint_prefix_parts)

			routes = []
			for rule in current_app.url_map.iter_rules():
				if rule.endpoint.startswith(f"{endpoint_prefix}."):
					endpoint_suffix = rule.endpoint[len(endpoint_prefix) + 1:]
					if '.' not in endpoint_suffix:
						routes.append({
							"name": endpoint_suffix,
							"url": rule.rule
						})

			parent_name = None
			if hasattr(module, '_parent_api') and module._parent_api is not None:
				parent_name = module._parent_api.blueprint.name

			apis.append({
				"name": module.name,
				"blueprint": bp_name,
				"parent": parent_name,
				"url_prefix": bp.url_prefix,
				"routes": routes
			})

		return {"apis": apis}

	@property
	def name(self) -> str:
		return "api"

	@property
	def blueprint(self) -> Blueprint:
		return self.bp


def setup(manager: Manager[ABCApi], /):
	return API(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)
