from typing import TYPE_CHECKING, cast, Any
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from ._base_service import ABCService
from ._manager import Manager
from .migrations import Service as Migrations
import json
import sqlite3


_SETTINGS = {}
class SENTINEL:
	def __eq__(self, *a): return False
	def __lt__(self, *a): return False
	def __le__(self, *a): return False
	def __gt__(self, *a): return False
	def __ge__(self, *a): return False
	def __bool__(self, *a): return False

_SENTINEL = SENTINEL()

class _SettingsRegistry[U]:
	def __getitem__[T](self, key: type[T]) -> '_SettingsRegistry[T]':
		return cast('_SettingsRegistry[T]', self)

	def __getattr__(self, key) -> U:
		return _SETTINGS.get(key, _SENTINEL)


class SettingDefinition:
	"""
	Helper class to define a setting with all its metadata in one place.

	Usage:
		setting = SettingDefinition(
			key="my_setting",
			default="default_value",
			description="What this setting does",
			valid_values=["option1", "option2"],
			options={"option1": "Description of option1"},
			examples=["example1", "example2"]
		)
	"""

	def __init__(
		self,
		key: str,
		default: Any,
		description: str,
		*,
		valid_values: list[str] | None = None,
		options: dict[str, str] | None = None,
		examples: list[str] | None = None,
		type_name: str = "string"
	):
		self.key = key
		self.default = default
		self.description = description
		self.valid_values = valid_values
		self.options = options
		self.examples = examples
		self.type_name = type_name

	def get_value[T](self, registry: _SettingsRegistry[T]) -> T:
		"""Get the value from settings registry or return default."""
		value = getattr(registry, self.key)
		if value is _SENTINEL or not value:
			return self.default
		return value

	def to_schema_dict(self) -> dict:
		"""Convert this definition to a schema dictionary entry."""
		schema = {
			"type": self.type_name,
			"default": self.default,
			"description": self.description
		}

		if self.valid_values:
			schema["valid_values"] = self.valid_values

		if self.options:
			schema["options"] = self.options

		if self.examples:
			schema["examples"] = self.examples

		return schema


# Define all settings in one place
SETTINGS_DEFINITIONS = [
	SettingDefinition(
		key="db",
		default=":memory:",
		description="Database file path or :memory: for in-memory database",
		examples=[":memory:", "app.db", "/path/to/database.db"]
	),
	SettingDefinition(
		key="prometheus",
		default="disabled",
		description="What type of prometheus metric registry to use",
		valid_values=["global", "custom", "disabled"],
		options={
			"global": "Use the global Prometheus registry",
			"custom": "Use a custom registry (recommended)",
			"disabled": "Disable Prometheus metrics"
		}
	),
	SettingDefinition(
		key="metrics",
		default="disabled",
		description="Whether to enable middleware-based metrics tracking",
		valid_values=["enabled", "disabled"],
		options={
			"enabled": "Enable custom metrics tracking with detailed statistics",
			"disabled": "Disable custom metrics tracking"
		}
	),
	SettingDefinition(
		key="redis_host",
		default="localhost",
		description="Redis server hostname or IP address",
		examples=["localhost", "127.0.0.1", "redis.example.com"],
		type_name="string"
	),
	SettingDefinition(
		key="redis_port",
		default=6379,
		description="Redis server port number",
		examples=[6379, 6380],
		type_name="integer"
	),
	SettingDefinition(
		key="redis_db",
		default=0,
		description="Redis database number to use",
		examples=[0, 1, 2],
		type_name="integer"
	),
	SettingDefinition(
		key="redis_password",
		default=None,
		description="Redis server password (optional, None for no authentication)",
		examples=[None, "your_password_here"],
		type_name="string"
	),
	SettingDefinition(
		key="task_worker_count",
		default=5,
		description="Number of concurrent task worker threads",
		examples=[1, 5, 10],
		type_name="integer"
	),
	SettingDefinition(
		key="task_cleanup_days",
		default=7,
		description="Days to keep completed/failed tasks before cleanup",
		examples=[1, 7, 30],
		type_name="integer"
	),
	SettingDefinition(
		key="task_workers_enabled",
		default=False,
		description="Whether to enable task workers in this process (important for WSGI environments)",
		valid_values=[True, False],
		options={
			"true": "Enable workers in this process (use for dedicated task worker or development)",
			"false": "Disable workers (recommended for WSGI worker processes)"
		},
		type_name="boolean"
	),
	SettingDefinition(
		key="task_worker_lock_file",
		default="/tmp/task_worker.lock",
		description="Path to lock file for preventing multiple worker processes",
		examples=["/tmp/task_worker.lock", "/var/run/app/task_worker.lock"],
		type_name="string"
	),
]

# Create a lookup dict for quick access
_SETTINGS_BY_KEY = {s.key: s for s in SETTINGS_DEFINITIONS}

class Service(ABCService):
	def __init__(self):
		self.r = _SettingsRegistry()
		with open("settings.json", 'r') as f:
			global _SETTINGS
			_SETTINGS = json.load(f)

	@property
	def name(self) -> str:
		return "settings"

	@property
	def ready(self) -> bool:
		return True

	@property
	def db(self) -> str:
		return _SETTINGS_BY_KEY["db"].get_value(self.r[str])

	@property
	def prometheus(self) -> str:
		return _SETTINGS_BY_KEY["prometheus"].get_value(self.r[str])

	@property
	def metrics(self) -> str:
		return _SETTINGS_BY_KEY["metrics"].get_value(self.r[str])

	@property
	def redis_host(self) -> str:
		return _SETTINGS_BY_KEY["redis_host"].get_value(self.r[str])

	@property
	def redis_port(self) -> int:
		return _SETTINGS_BY_KEY["redis_port"].get_value(self.r[int])

	@property
	def redis_db(self) -> int:
		return _SETTINGS_BY_KEY["redis_db"].get_value(self.r[int])

	@property
	def redis_password(self) -> str | None:
		return _SETTINGS_BY_KEY["redis_password"].get_value(self.r[str])

	@property
	def task_worker_count(self) -> int:
		return _SETTINGS_BY_KEY["task_worker_count"].get_value(self.r[int])

	@property
	def task_cleanup_days(self) -> int:
		return _SETTINGS_BY_KEY["task_cleanup_days"].get_value(self.r[int])

	@property
	def task_workers_enabled(self) -> bool:
		return _SETTINGS_BY_KEY["task_workers_enabled"].get_value(self.r[bool])

	@property
	def task_worker_lock_file(self) -> str:
		return _SETTINGS_BY_KEY["task_worker_lock_file"].get_value(self.r[str])

	@staticmethod
	def get_default_settings() -> dict:
		"""
		Get the default settings dictionary.

		Returns:
			Dictionary with default values for all settings
		"""
		return {s.key: s.default for s in SETTINGS_DEFINITIONS}

	@staticmethod
	def get_settings_schema() -> dict:
		"""
		Get the settings schema with documentation.

		Returns:
			Dictionary describing all available settings, their types, defaults, and valid values
		"""
		return {s.key: s.to_schema_dict() for s in SETTINGS_DEFINITIONS}

	@staticmethod
	def write_default_settings(filepath: str = "settings.json", *, overwrite: bool = False) -> bool:
		"""
		Write default settings to a JSON file.

		Args:
			filepath: Path to the settings file (default: "settings.json")
			overwrite: If True, overwrite existing file; if False, raise error if file exists

		Returns:
			True if file was written, False if file exists and overwrite=False

		Raises:
			FileExistsError: If file exists and overwrite=False
		"""
		import os

		if os.path.exists(filepath) and not overwrite:
			raise FileExistsError(f"Settings file already exists: {filepath}")

		defaults = Service.get_default_settings()

		with open(filepath, 'w') as f:
			json.dump(defaults, f, indent=2)

		return True

	@staticmethod
	def write_settings_schema(filepath: str = "settings.schema.json") -> bool:
		"""
		Write settings schema documentation to a JSON file.

		Args:
			filepath: Path to the schema file (default: "settings.schema.json")

		Returns:
			True if file was written
		"""
		schema = Service.get_settings_schema()

		with open(filepath, 'w') as f:
			json.dump(schema, f, indent=2)

		return True


def setup(manager: Manager[ABCService], /):
	return Service()

if TYPE_CHECKING:
	setup = validate_setup(setup)
