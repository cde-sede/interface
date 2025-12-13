from typing import TYPE_CHECKING, Any, Optional, cast
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from ._base_service import ABCService
from ._manager import Manager
from .settings import Service as Settings
import redis
from redis import Redis
import json


class Service(ABCService):
	def __init__(self, manager: Manager[ABCService]):
		self.manager = manager
		self.settings = self.manager.get[Settings]('settings')

		# Get Redis connection details from settings
		# Settings now provide defaults via SettingDefinition
		redis_host = self.settings.redis_host
		redis_port = self.settings.redis_port
		redis_db = self.settings.redis_db
		redis_password = self.settings.redis_password

		# Initialize Redis connection (synchronous client)
		self._redis: Redis = redis.Redis(
			host=redis_host,
			port=redis_port,
			db=redis_db,
			password=redis_password,
			decode_responses=True,
			socket_connect_timeout=5,
			socket_timeout=5
		)

		self._ready = self._check_connection()

	def _check_connection(self) -> bool:
		"""Check if Redis connection is available."""
		try:
			cast(bool, self._redis.ping())
			return True
		except (redis.ConnectionError, redis.TimeoutError):
			return False

	@property
	def name(self) -> str:
		return "cache"

	@property
	def ready(self) -> bool:
		return self._ready

	def get(self, key: str, default: Any = None) -> Any:
		"""Get a value from cache."""
		if not self._ready:
			return default

		try:
			value = cast(str, self._redis.get(key))
			if value is None:
				return default

			# Try to deserialize JSON
			try:
				return json.loads(value)
			except (json.JSONDecodeError, TypeError):
				return value
		except Exception:
			return default

	def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
		"""
		Set a value in cache.

		Args:
			key: Cache key
			value: Value to cache (will be JSON serialized if not a string)
			ttl: Time to live in seconds (optional)

		Returns:
			True if successful, False otherwise
		"""
		if not self._ready:
			return False

		try:
			# Serialize non-string values to JSON
			if not isinstance(value, str):
				value = json.dumps(value)

			if ttl:
				return cast(bool, self._redis.setex(key, ttl, value))
			else:
				return cast(bool, self._redis.set(key, value))
		except Exception:
			return False

	def delete(self, *keys: str) -> int:
		"""
		Delete one or more keys from cache.

		Returns:
			Number of keys deleted
		"""
		if not self._ready or not keys:
			return 0

		try:
			return cast(int, self._redis.delete(*keys))
		except Exception:
			return 0

	def exists(self, *keys: str) -> int:
		"""
		Check if one or more keys exist in cache.

		Returns:
			Number of keys that exist
		"""
		if not self._ready or not keys:
			return 0

		try:
			return cast(int, self._redis.exists(*keys))
		except Exception:
			return 0

	def expire(self, key: str, ttl: int) -> bool:
		"""
		Set expiration time for a key.

		Args:
			key: Cache key
			ttl: Time to live in seconds

		Returns:
			True if successful, False otherwise
		"""
		if not self._ready:
			return False

		try:
			return cast(bool, self._redis.expire(key, ttl))
		except Exception:
			return False

	def clear(self, pattern: str = "*") -> int:
		"""
		Clear cache keys matching a pattern.

		Args:
			pattern: Pattern to match (default: "*" for all keys)

		Returns:
			Number of keys deleted
		"""
		if not self._ready:
			return 0

		try:
			keys = list(self._redis.scan_iter(pattern))
			if keys:
				return cast(int, self._redis.delete(*keys))
			return 0
		except Exception:
			return 0

	def incr(self, key: str, amount: int = 1) -> Optional[int]:
		"""
		Increment a numeric value in cache.

		Returns:
			New value or None if failed
		"""
		if not self._ready:
			return None

		try:
			return cast(int, self._redis.incrby(key, amount))
		except Exception:
			return None

	def decr(self, key: str, amount: int = 1) -> Optional[int]:
		"""
		Decrement a numeric value in cache.

		Returns:
			New value or None if failed
		"""
		if not self._ready:
			return None

		try:
			return cast(int, self._redis.decrby(key, amount))
		except Exception:
			return None


def setup(manager: Manager[ABCService], /):
	require("settings")
	return Service(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)
