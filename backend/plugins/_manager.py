from flask import Blueprint
from ._base_plugin import ABCPlugin
from types import ModuleType
import sys

bp = Blueprint("plugins", __name__)

from ..manager import Manager, ModuleLoadError

def _check(m: ModuleType):
	if not hasattr(m, 'setup'):
		raise ModuleLoadError("Setup function is required for plugins")
	instance = getattr(m, 'setup')(manager)
	if not isinstance(instance, ABCPlugin):
		raise ModuleLoadError("Setup function must return a valid Plugin")
	return instance


manager = Manager[ABCPlugin](__name__, checker=_check)
