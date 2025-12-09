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

	@describe("Lists all registered API modules and their routes")
	def list_apis(self):
		"""Returns a comprehensive list of all loaded API modules with their blueprints and available routes."""

		apis = []
		for module in self.manager.modules:
			# Get routes for this blueprint from the app's url_map
			bp = module.blueprint
			bp_name = bp.name

			# For nested blueprints, check if blueprint name appears in endpoint
			routes = []
			for rule in current_app.url_map.iter_rules():
				endpoint_parts = rule.endpoint.split('.')
				# Check if this endpoint belongs to this blueprint
				# For direct blueprints: "api." or first part is "api"
				# For nested blueprints: "api.v1." or second part is "v1"
				if rule.endpoint.startswith(f"{bp_name}.") or \
				   endpoint_parts[0] == bp_name or \
				   (len(endpoint_parts) > 1 and endpoint_parts[-2] == bp_name):
					routes.append(rule.rule)

			apis.append({"name": module.name, "blueprint": bp_name, "routes": routes})

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
