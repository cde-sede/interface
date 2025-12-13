import importlib.util
from importlib.machinery import ModuleSpec
import sys
import threading
import traceback
from types import ModuleType
from typing import Any, cast, overload, TypedDict
from collections.abc import Callable
from pathlib import Path


class _ModuleSpec(TypedDict):
	spec: ModuleSpec
	file: Path
	relative_path: Path
	module_path: str

class ModuleLoadError(Exception):
	pass

class _Exports[T](type):
	def __getitem__[U](self, t: type[U]) -> 'Exports[U]':
		return cast('Exports[U]', self())

class Exports[T](metaclass=_Exports):
	_all: dict[str, Any] = {}

	def __init__(self):
		pass
	@classmethod
	def export(cls, s: str, obj: Any):
		if s in cls._all:
			raise ValueError()
		cls._all[s] = obj

	@classmethod
	def get(cls, s: str) -> T:
		return cls._all[s]

class _TypedGetter[T, U]:
	"""Helper class for type-safe manager.get[Type]() calls."""
	def __init__(self, manager: 'Manager[T]'):
		self._manager = manager

	def __call__(self, path: str, *, use_cache: bool = True) -> U:
		return cast(U, self._manager._get_impl(path, use_cache=use_cache))

class _BoundGet[T]:
	"""Bound get method that supports subscripting for type hints."""
	def __init__(self, manager: 'Manager[T]'):
		self._manager = manager

	def __getitem__[U](self, t: type[U]) -> _TypedGetter[T, U]:
		"""Returns a typed getter: manager.get[AuthPlugin]('path')"""
		return _TypedGetter[T, U](self._manager)

	def __call__(self, path: str, *, use_cache: bool = True):
		"""Untyped get: manager.get('path')"""
		return self._manager._get_impl(path, use_cache=use_cache)

class _GetDescriptor:
	"""Descriptor that makes get subscriptable."""
	@overload
	def __get__(self, obj: None, objtype: type | None = None) -> '_GetDescriptor': ...

	@overload
	def __get__[T](self, obj: 'Manager[T]', objtype: type | None = None) -> '_BoundGet[T]': ...

	def __get__(self, obj, objtype=None) -> '_GetDescriptor | _BoundGet':
		if obj is None:
			return self
		return _BoundGet(obj)

class Manager[T]:
	__REGISTRY: 'dict[str, Manager]' = {}
	exports = Exports
	get = _GetDescriptor()

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
		self._modules_specs: dict[str, _ModuleSpec] = {}
		self._get_cache: dict[str, Any] = {}
		self._cache_lock = threading.Lock()

		# Determine if lookup_dir is a module name or file path
		if '/' in lookup_dir:
			# File path: "backend/plugins" -> package "backend.plugins"
			self.lookup_dir = Path(lookup_dir)
			self._caller_package = lookup_dir.replace('/', '.')
		else:
			# Module name: "backend.plugins.manager" -> package "backend.plugins"
			# Extract package (remove module name if present, assuming it ends with .manager or similar)
			parts = lookup_dir.split('.')
			self._caller_package = '.'.join(parts[:-1]) if len(parts) > 1 else lookup_dir
			self.lookup_dir = Path(self._caller_package.replace('.', '/'))

		# Register using a meaningful identifier (second part for nested packages, first part otherwise)
		package_parts = self._caller_package.split('.')
		self._registry_key = package_parts[1] if len(package_parts) > 1 else package_parts[0]
		self._base_package = package_parts[0]
		Manager.__REGISTRY[self._registry_key] = self

		self._discover_modules()

	def _get_impl(self, path: str, *, use_cache: bool = True):
		"""
		Get a module by path, supporting cross-manager lookups and directory structure.
		Results are cached for performance.

		Args:
			path: Module path (e.g., 'Example', 'models.user', 'services.db', 'Example.attr')
			use_cache: If True, use cached results; if False, bypass cache

		Examples:
			manager.get('Example') - Get module with name='Example' from current manager
			manager.get('models.user') - Get module at models/user.py
			manager.get[AuthPlugin]('plugins.auth') - Type-safe cross-manager lookup
			manager.get('plugins') - Get the plugins manager instance
			manager.get('services.db') - Get 'db' service from services manager
			manager.get('Example.attr') - Get attribute from module
			manager.get('models.user.SomeClass') - Get SomeClass from models/user.py
		"""
		# Check cache first
		if use_cache:
			with self._cache_lock:
				if path in self._get_cache:
					return self._get_cache[path]

		parts = path.split('.')

		# Check if first part is a registered manager (cross-manager lookup)
		if parts[0] in Manager.__REGISTRY and parts[0] != self._registry_key:
			target_manager = Manager.__REGISTRY[parts[0]]
			if len(parts) == 1:
				# Return the manager itself
				result = target_manager
			else:
				# Delegate to target manager for the rest
				result = target_manager._get_impl('.'.join(parts[1:]), use_cache=use_cache)
		else:
			# Local lookup - try progressively longer module paths
			# This allows "models.user" to find modules/user.py
			# and "models.user.attr" to get the attr from modules/user.py
			obj = None
			remaining_parts = []

			# Try from longest to shortest path
			for i in range(len(parts), 0, -1):
				potential_module_path = '.'.join(parts[:i])
				try:
					obj = self._get_by_name_or_path(potential_module_path)
					remaining_parts = parts[i:]
					break
				except KeyError:
					continue

			if obj is None:
				raise KeyError(f"No module found for path '{path}'")

			# Traverse remaining path as attributes
			for attr in remaining_parts:
				obj = getattr(obj, attr)

			result = obj

		# Cache the result
		if use_cache:
			with self._cache_lock:
				self._get_cache[path] = result

		return result

	def invalidate_cache(self, path: str) -> int:
		"""
		Invalidate cached get() results for a specific path and all sub-paths.

		Examples:
			manager.invalidate_cache('Example')
			# Removes: 'Example', 'Example.attr', 'Example.nested.value'

			manager.invalidate_cache('services.db')
			# Removes: 'services.db'

		Args:
			path: The path to invalidate (and all paths starting with it)

		Returns:
			Number of cache entries removed
		"""
		with self._cache_lock:
			keys_to_remove = [
				k for k in self._get_cache
				if k == path or k.startswith(path + '.')
			]
			for key in keys_to_remove:
				del self._get_cache[key]
			return len(keys_to_remove)

	def clear_cache(self) -> int:
		"""
		Clear all cached get() results for this manager.

		Returns:
			Number of cache entries removed
		"""
		with self._cache_lock:
			count = len(self._get_cache)
			self._get_cache.clear()
			return count

	def _get_by_name(self, name: str) -> T:
		"""Get a module by its name property."""
		for module in self._modules.values():
			if module.name == name:
				return module
		raise KeyError(f"No module with name '{name}' found")

	def _get_by_name_or_path(self, name_or_path: str) -> T:
		"""Get a module by its name property or module path."""
		# First try by module path (direct lookup in specs)
		if name_or_path in self._modules_specs:
			return self.load(name_or_path)

		# Then try by name property
		for module_path, module in self._modules.items():
			if module.name == name_or_path:
				return module

		raise KeyError(f"No module with name or path '{name_or_path}' found")

	@property
	def modules(self):
		"""Return tuple of loaded module instances."""
		return tuple(self._modules.values())

	@property
	def specs(self) -> tuple[_ModuleSpec, ...]:
		return tuple(self._modules_specs.values())

	def _require(self, name: str):
		return self.load(name)

	def _discover_modules(self):
		for file in self.lookup_dir.rglob("[!_]*.py"):
			# Calculate relative path from lookup_dir to preserve directory structure
			relative_path = file.relative_to(self.lookup_dir)

			# Convert path to module path: models/user.py -> models.user
			module_path = str(relative_path.with_suffix('')).replace('/', '.')

			spec = importlib.util.spec_from_file_location(
				module_path, file
			)

			assert spec is not None
			self._modules_specs[module_path] = {
				"spec": spec,
				"file": file,
				"relative_path": relative_path,
				"module_path": module_path,
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
		relative_path = spec_info["relative_path"]
		if relative_path.parent == Path('.'):
			# File in root directory
			module.__package__ = self._caller_package
		else:
			# File in subdirectory: add subdirectory to package path
			subdir_package = str(relative_path.parent).replace('/', '.')
			module.__package__ = f"{self._caller_package}.{subdir_package}"

		module.__dict__.update({
			'manager': self,
			'require': self._require,
			'inject': self._dependencies
		})

		try:
			assert spec.loader is not None
			spec.loader.exec_module(module)
		except Exception as e:
			traceback.print_exception(e)
			print('-' * 10)
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
