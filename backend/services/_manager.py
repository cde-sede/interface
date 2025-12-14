from flask import Blueprint
from ._base_service import ABCService
from types import ModuleType

bp = Blueprint("services", __name__)

from ..manager import Manager, ModuleLoadError

def _check(m: ModuleType):
	if not hasattr(m, 'setup'):
		raise ModuleLoadError("Setup function is required for service modules", m)
	instance = getattr(m, 'setup')(manager)
	if not isinstance(instance, ABCService):
		raise ModuleLoadError("Setup function must return a valid ABCService")
	return instance


manager = Manager[ABCService](__name__, checker=_check)

def reload_all_services():
	"""Reload all service modules."""
	print("\n=== Reloading Services ===")
	return manager.reload_all()
