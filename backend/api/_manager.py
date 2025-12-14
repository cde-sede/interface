from flask import Blueprint
from ._base_api import ABCApi
from types import ModuleType

bp = Blueprint("api", __name__)

from ..manager import Manager, ModuleLoadError

def _check(m: ModuleType):
	if not hasattr(m, 'setup'):
		raise ModuleLoadError("Setup function is required for API modules", m)
	instance = getattr(m, 'setup')(manager)
	if not isinstance(instance, ABCApi):
		raise ModuleLoadError("Setup function must return a valid ABCApi")
	return instance


manager = Manager[ABCApi](__name__, checker=_check)

def unregister_blueprints(app, *blueprint_names):
	"""
	Unregister blueprints from the Flask app.

	This removes blueprints from app.blueprints and clears their routes
	from the URL map and view functions.

	Args:
		app: Flask application instance
		*blueprint_names: Names of blueprints to unregister
	"""
	print(f"Unregistering blueprints: {blueprint_names}")

	# Remove blueprints from registry
	for name in blueprint_names:
		if name in app.blueprints:
			del app.blueprints[name]
			print(f"  Removed blueprint '{name}' from registry")

	# Rebuild URL map without the blueprint routes
	# We need to filter out rules that belong to the blueprints being removed
	new_rules = []
	removed_count = 0

	for rule in app.url_map.iter_rules():
		# Check if this rule belongs to a blueprint we're removing
		endpoint_parts = rule.endpoint.split('.')
		if len(endpoint_parts) > 1 and endpoint_parts[0] in blueprint_names:
			# This rule belongs to a blueprint being removed
			removed_count += 1
			# Also remove from view_functions
			if rule.endpoint in app.view_functions:
				del app.view_functions[rule.endpoint]
		else:
			# Keep this rule
			new_rules.append(rule)

	print(f"  Removed {removed_count} routes")

	# Rebuild the URL map with only the kept rules
	app.url_map._rules.clear()
	app.url_map._rules_by_endpoint.clear()

	for rule in new_rules:
		app.url_map.add(rule)

	print("Blueprint unregistration complete")

def reload_all_apis(app):
	"""
	Reload all API modules with proper blueprint handling.

	This unregisters existing blueprints, reloads the API modules,
	and re-registers the blueprints.

	Args:
		app: Flask application instance
	"""
	print("\n=== Reloading APIs ===")

	# Get list of loaded API modules
	loaded_apis = list(manager._modules.keys())
	blueprint_names = []

	# Collect blueprint names before unloading
	for api_name in loaded_apis:
		try:
			api_instance = manager._modules[api_name]
			if hasattr(api_instance, 'blueprint'):
				blueprint_names.append(api_instance.blueprint.name)
		except Exception as e:
			print(f"Warning: Could not get blueprint name for {api_name}: {e}")

	# Unregister all blueprints
	if blueprint_names:
		unregister_blueprints(app, *blueprint_names)

	# Reload all API modules
	results = manager.reload_all()

	# Re-register blueprints
	print("\n=== Re-registering Blueprints ===")
	for api_name in results.keys():
		try:
			api_instance = manager.get[ABCApi](api_name)
			app.register_blueprint(api_instance.blueprint)
			print(f"  Registered blueprint '{api_instance.blueprint.name}'")
		except Exception as e:
			print(f"ERROR: Failed to register blueprint for {api_name}: {e}")

	return results
