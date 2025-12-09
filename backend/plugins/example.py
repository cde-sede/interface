# Test file to verify builtins are recognized
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from _injected import *

from ._base_plugin import ABCPlugin
from ._manager import Manager
from flask import Blueprint

class Plugin(ABCPlugin):
	@property
	def name(self) -> str:
		return "Example"

	@property
	def blueprint(self) -> Blueprint:
		return Blueprint("example", __name__)

# These should NOT show LSP errors
def setup(manager: Manager[ABCPlugin], /):
	return Plugin()

if TYPE_CHECKING:
	setup = validate_setup(setup)

