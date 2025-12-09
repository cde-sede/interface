from flask import Blueprint
from ._base_api import ABCApi
from types import ModuleType

bp = Blueprint("api", __name__)

from ..manager import Manager, ModuleLoadError

def _check(m: ModuleType):
	if not hasattr(m, 'setup'):
		raise ModuleLoadError("Setup function is required for API modules")
	instance = getattr(m, 'setup')(manager)
	if not isinstance(instance, ABCApi):
		raise ModuleLoadError("Setup function must return a valid ABCApi")
	return instance


manager = Manager[ABCApi](__name__, checker=_check)
