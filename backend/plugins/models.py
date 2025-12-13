from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from collections.abc import Callable
from ._base_plugin import ABCPlugin
from ._manager import Manager
from .models import ABCModel, File

class Plugin(ABCPlugin):
	def __init__(self, manager: Manager[ABCPlugin]):
		self.manager = manager

		self._models: dict[str, ABCModel] = {}
		specs = [i['module_path'] for i in self.manager.specs if i['module_path'].startswith('models.')]
		for i in specs:
			self._models[i] = manager.get[ABCModel](i)

	@property
	def files(self) -> File:
		return cast(File, self._models['files'])

	@property
	def name(self) -> str:
		return "models"

def setup(manager: Manager[ABCPlugin], /):
	return Plugin(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)

