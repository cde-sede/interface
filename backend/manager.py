import importlib.util
import pathlib
import sys
from types import ModuleType
from collections.abc import Callable

class ModuleLoadError(Exception):
	pass

class Manager[T]:
	__REGISTRY: 'dict[str, Manager]' = {}

	def __new__(cls, *args, **kwags):
		return super().__new__(cls)

	@classmethod
	def get_manager(cls, key: str) -> 'Manager':
		"""Get a manager instance from the registry by its key."""
		if key not in cls.__REGISTRY:
			raise KeyError(f"No manager registered with key '{key}'")
		return cls.__REGISTRY[key]

	def __init__(self, lookup_dir: str, *,
			  checker: Callable[[ModuleType], T], dependencies: dict | None = None):
		"""
		checker: function that takes the module and returns the instance T@Manager
					Raises ModuleLoadError if anything wrong happens
		dependencies: injectable objects accessible by modules
					  e.g. {"logger": logger, "db": db_instance}

		lookup_dir: Can be either:
			- A module name (e.g., __name__ = "backend.plugins.manager")
			- A file path (e.g., "backend/plugins")
		"""
		self.checker = checker
		self._dependencies = dependencies or {}
		self._modules: dict[str, T] = {}
		self._modules_specs = {}

		# Determine if lookup_dir is a module name or file path
		if '/' in lookup_dir:
			# File path: "backend/plugins" -> package "backend.plugins"
			self.lookup_dir = pathlib.Path(lookup_dir)
			self._caller_package = lookup_dir.replace('/', '.')
		else:
			# Module name: "backend.plugins.manager" -> package "backend.plugins"
			# Extract package (remove module name if present, assuming it ends with .manager or similar)
			parts = lookup_dir.split('.')
			self._caller_package = '.'.join(parts[:-1]) if len(parts) > 1 else lookup_dir
			self.lookup_dir = pathlib.Path(self._caller_package.replace('.', '/'))

		# Register using a meaningful identifier (second part for nested packages, first part otherwise)
		package_parts = self._caller_package.split('.')
		self._registry_key = package_parts[1] if len(package_parts) > 1 else package_parts[0]
		self._base_package = package_parts[0]
		Manager.__REGISTRY[self._registry_key] = self

		self._discover_modules()

	def get(self, path: str):
		"""
		Get a module by path, supporting cross-manager lookups.

		Examples:
			manager.get('Example') - Get module with name='Example' from current manager
			manager.get('plugins') - Get the plugins manager instance
			manager.get('services.db') - Get 'db' service from services manager
			manager.get('Example.attr') - Get attribute from module
		"""
		parts = path.split('.')

		# Check if first part is a registered manager (cross-manager lookup)
		if parts[0] in Manager.__REGISTRY and parts[0] != self._registry_key:
			target_manager = Manager.__REGISTRY[parts[0]]
			if len(parts) == 1:
				# Return the manager itself
				return target_manager
			else:
				# Get module from the target manager
				obj = target_manager._get_by_name(parts[1])
				remaining = parts[2:]
		else:
			# Local lookup by name property
			obj = self._get_by_name(parts[0])
			remaining = parts[1:]

		# Traverse remaining path
		for attr in remaining:
			obj = getattr(obj, attr)
		return obj

	def _get_by_name(self, name: str) -> T:
		"""Get a module by its name property."""
		for module in self._modules.values():
			if module.name == name:
				return module
		raise KeyError(f"No module with name '{name}' found")

	@property
	def modules(self):
		"""Return tuple of loaded module instances."""
		return tuple(self._modules.values())

	@property
	def specs(self):
		return tuple(self._modules_specs)

	def _require(self, name: str):
		return self.load(name)

	def _discover_modules(self):
		for file in self.lookup_dir.iterdir():
			# Skip files starting with underscore or not ending in .py
			if file.name.startswith('_') or not file.name.endswith('.py'):
				continue

			module_name = file.stem  # filename without extension

			spec = importlib.util.spec_from_file_location(
				module_name, file
			)
			self._modules_specs[module_name] = {
				"spec": spec,
				"file": file,
			}

	def load(self, name: str):
		if name in self._modules:
			return self._modules[name]

		if name not in self._modules_specs:
			raise ModuleLoadError(f"No module named '{name}' found")

		spec_info = self._modules_specs[name]
		spec = spec_info["spec"]
		module = importlib.util.module_from_spec(spec)

		# Set package for relative imports to work
		module.__package__ = self._caller_package

		module.__dict__.update({
			'manager': self,
			'require': self._require,
			"inject": self._dependencies
		})

		try:
			spec.loader.exec_module(module)
		except Exception as e:
			raise ModuleLoadError(f"Failed to load module {name}: {e}")

		instance = self.checker(module)

		self._modules[name] = instance
		return instance

	def list_plugins(self):
		"""List all discovered plugins by their name property (for loaded) or module name (for unloaded)."""
		result = []
		for module_name in self._modules_specs.keys():
			# Use the name property if loaded, otherwise use module name
			if module_name in self._modules:
				display_name = self._modules[module_name].name
			else:
				display_name = module_name
			result.append(display_name)
		return result
