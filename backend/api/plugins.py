from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from ._base_api import ABCApi, describe
from ._manager import Manager
from flask import Blueprint


class PluginsAPI(ABCApi):
	def __init__(self, manager: Manager[ABCApi], v1: ABCApi):
		self.manager = manager
		self.v1 = v1
		self.bp = self.create_blueprint("plugins", parent=v1, url_prefix="/plugins")

		# Add routes
		self.bp.add_url_rule("/", view_func=self.list_plugins)

	@describe("Lists all loaded plugins")
	def list_plugins(self):
		"""Returns information about all currently loaded plugins in the system."""
		plugin_manager = self.manager.get('plugins')
		assert isinstance(plugin_manager, Manager)

		plugins = []
		for module_name, plugin in plugin_manager._modules.items():
			plugins.append({
				"module_name": module_name,
				"name": plugin.name
			})

		return {"plugins": plugins, "count": len(plugins)}

	@property
	def name(self) -> str:
		return "plugins"

	@property
	def blueprint(self) -> Blueprint:
		return self.bp


def setup(manager: Manager[ABCApi], /):
	v1 = require('v1')
	return PluginsAPI(manager, v1)

if TYPE_CHECKING:
	setup = validate_setup(setup)
