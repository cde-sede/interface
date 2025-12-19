from __future__ import annotations
from typing import TYPE_CHECKING, cast, Optional
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup
	from .migrations import Service as Migrations
	from .logs import Service as Logs

from ._base_service import ABCService
from ._manager import Manager
from .settings import Service as Settings
import sqlite3
import time
import json
import os
import threading
import atexit
from collections import defaultdict
from threading import Lock, Thread, Event
from pathlib import Path


# Global metrics storage for database operations
class DBMetrics:
	"""Thread-safe database metrics collector"""
	def __init__(self):
		self.lock = Lock()
		self.query_count = 0
		self.error_count = 0
		self.total_time = 0.0
		self.query_times = []
		self.max_query_time = 0.0
		self.min_query_time = float('inf')
		self.active_connections = 0

		# Track individual queries (keep last 100)
		self.recent_queries = []

		# Track query patterns (aggregated by normalized query)
		self.query_patterns = defaultdict(lambda: {
			'count': 0,
			'total_time': 0.0,
			'error_count': 0,
			'last_execution': None,
			'example_query': None  # Store one example with actual parameters
		})

	def record_query(self, execution_time: float, success: bool = True):
		"""Record a query execution (transaction-level)"""
		with self.lock:
			self.query_count += 1
			if success:
				self.total_time += execution_time
				self.query_times.append(execution_time)
				# Keep only last 1000 queries for percentile calculation
				if len(self.query_times) > 1000:
					self.query_times.pop(0)
				self.max_query_time = max(self.max_query_time, execution_time)
				if execution_time > 0:
					self.min_query_time = min(self.min_query_time, execution_time)
			else:
				self.error_count += 1

	def record_individual_query(self, query: str, params: tuple, execution_time: float,
	                            success: bool = True, error: Optional[str] = None):
		"""Record an individual SQL query"""
		with self.lock:
			# Normalize query (replace ? placeholders and values for pattern matching)
			normalized_query = self._normalize_query(query)

			# Update pattern stats
			pattern = self.query_patterns[normalized_query]
			pattern['count'] += 1
			if success:
				pattern['total_time'] += execution_time
			else:
				pattern['error_count'] += 1
			pattern['last_execution'] = time.time()

			# Store one example query with actual parameters
			if pattern['example_query'] is None:
				pattern['example_query'] = {
					'query': query,
					'params': params
				}

			# Track recent queries
			self.recent_queries.append({
				'query': query,
				'params': params,
				'execution_time': execution_time,
				'success': success,
				'error': error,
				'timestamp': time.time()
			})

			# Keep only last 100 queries
			if len(self.recent_queries) > 100:
				self.recent_queries.pop(0)

	def _normalize_query(self, query: str) -> str:
		"""Normalize a query for pattern matching"""
		import re
		# Remove extra whitespace
		normalized = ' '.join(query.split())
		# Replace numbers with placeholder
		normalized = re.sub(r'\b\d+\b', 'N', normalized)
		# Replace string literals with placeholder
		normalized = re.sub(r"'[^']*'", 'S', normalized)
		return normalized

	def get_stats(self) -> dict:
		"""Get current metrics stats"""
		with self.lock:
			if self.query_count == 0:
				return {
					'total_queries': 0,
					'errors': 0,
					'avg_query_time': 0.0,
					'max_query_time': 0.0,
					'min_query_time': 0.0,
					'p95_query_time': 0.0,
					'p99_query_time': 0.0,
					'active_connections': 0,
					'query_patterns': [],
					'recent_queries': []
				}

			sorted_times = sorted(self.query_times)
			count = len(sorted_times)

			p95_idx = int(count * 0.95)
			p99_idx = int(count * 0.99)

			# Format query patterns for display
			query_patterns_list = []
			for normalized_query, pattern_data in self.query_patterns.items():
				avg_time = pattern_data['total_time'] / max(pattern_data['count'] - pattern_data['error_count'], 1)
				example = pattern_data['example_query']
				query_patterns_list.append({
					'normalized_query': normalized_query,
					'count': pattern_data['count'],
					'total_time': pattern_data['total_time'],
					'avg_time': avg_time,
					'error_count': pattern_data['error_count'],
					'last_execution': pattern_data['last_execution'],
					'example_query': example['query'] if example else '',
					'example_params': repr(example['params']) if example else '()'
				})

			# Sort by count descending
			query_patterns_list.sort(key=lambda x: x['count'], reverse=True)

			return {
				'total_queries': self.query_count,
				'errors': self.error_count,
				'avg_query_time': self.total_time / max(self.query_count - self.error_count, 1),
				'max_query_time': self.max_query_time,
				'min_query_time': self.min_query_time if self.min_query_time != float('inf') else 0.0,
				'p95_query_time': sorted_times[p95_idx] if count > 0 else 0.0,
				'p99_query_time': sorted_times[p99_idx] if count > 0 else 0.0,
				'active_connections': self.active_connections,
				'query_patterns': query_patterns_list,
				'recent_queries': list(reversed(self.recent_queries))  # Most recent first
			}

	def increment_connections(self):
		"""Track active connection count"""
		with self.lock:
			self.active_connections += 1

	def decrement_connections(self):
		"""Track active connection count"""
		with self.lock:
			self.active_connections = max(0, self.active_connections - 1)

	def save_to_disk(self, filepath: str = "metrics/db_metrics.json"):
		"""Save metrics to disk"""
		with self.lock:
			# Create directory if it doesn't exist
			os.makedirs(os.path.dirname(filepath), exist_ok=True)

			# Convert defaultdict to regular dict for JSON serialization
			query_patterns_serializable = {}
			for key, value in self.query_patterns.items():
				query_patterns_serializable[key] = {
					'count': value['count'],
					'total_time': value['total_time'],
					'error_count': value['error_count'],
					'last_execution': value['last_execution'],
					'example_query': value['example_query']
				}

			data = {
				'query_count': self.query_count,
				'error_count': self.error_count,
				'total_time': self.total_time,
				'query_times': self.query_times,
				'max_query_time': self.max_query_time,
				'min_query_time': self.min_query_time if self.min_query_time != float('inf') else 0.0,
				'active_connections': self.active_connections,
				'recent_queries': self.recent_queries,
				'query_patterns': query_patterns_serializable
			}

			with open(filepath, 'w') as f:
				json.dump(data, f, indent=2)

	def load_from_disk(self, filepath: str = "metrics/db_metrics.json"):
		"""Load metrics from disk"""
		if not os.path.exists(filepath):
			return False

		try:
			with open(filepath, 'r') as f:
				data = json.load(f)

			with self.lock:
				self.query_count = data.get('query_count', 0)
				self.error_count = data.get('error_count', 0)
				self.total_time = data.get('total_time', 0.0)
				self.query_times = data.get('query_times', [])
				self.max_query_time = data.get('max_query_time', 0.0)
				min_time = data.get('min_query_time', 0.0)
				self.min_query_time = float('inf') if min_time == 0.0 and self.query_count == 0 else min_time
				self.active_connections = 0  # Reset active connections on load
				self.recent_queries = data.get('recent_queries', [])

				# Load query patterns back into defaultdict
				loaded_patterns = data.get('query_patterns', {})
				for key, value in loaded_patterns.items():
					self.query_patterns[key] = {
						'count': value['count'],
						'total_time': value['total_time'],
						'error_count': value['error_count'],
						'last_execution': value['last_execution'],
						'example_query': value['example_query']
					}

			return True
		except Exception as e:
			print(f"Failed to load DB metrics: {e}")
			return False


# Global instance
_db_metrics = DBMetrics()
# Load persisted metrics on startup
_db_metrics.load_from_disk()


# Metrics persistence manager
class MetricsPersistenceManager:
	"""Background thread that periodically saves all metrics to disk"""

	def __init__(self, interval: int = 300):  # Default: save every 5 minutes
		self.interval = interval
		self._stop_event = Event()
		self._thread = None
		self._running = False

	def start(self):
		"""Start the periodic saving thread"""
		if self._running:
			return

		self._running = True
		self._stop_event.clear()
		self._thread = Thread(target=self._save_loop, daemon=True)
		self._thread.start()

		# Register shutdown handler
		atexit.register(self.stop)

	def stop(self):
		"""Stop the periodic saving thread and perform final save"""
		if not self._running:
			return

		self._running = False
		self._stop_event.set()

		if self._thread and self._thread.is_alive():
			self._thread.join(timeout=5)

		# Perform final save on shutdown
		self._save_all_metrics()

	def _save_loop(self):
		"""Background loop that saves metrics periodically"""
		while not self._stop_event.wait(self.interval):
			self._save_all_metrics()

	def _save_all_metrics(self):
		"""Save all metrics to disk"""
		try:
			# Save DB metrics
			_db_metrics.save_to_disk()

			# Save model metrics
			try:
				from ..plugins.models._model import _model_metrics
				_model_metrics.save_to_disk()
			except Exception as e:
				print(f"Error saving model metrics: {e}")

			# Save API metrics (if service is initialized)
			try:
				# Import at runtime to avoid circular dependencies
				from ._manager import Manager as ServiceManager
				from .metrics import MetricsService
				from . import ABCService

				# Try to get the metrics service if it exists
				# This is a bit hacky but works without circular dependencies
				import sys
				app_module = sys.modules.get('backend.app')
				if app_module and hasattr(app_module, 'services'):
					services_manager = app_module.services
					try:
						metrics_service = services_manager.get('metrics')
						if hasattr(metrics_service, 'save_to_disk'):
							metrics_service.save_to_disk()
					except:
						pass
			except Exception as e:
				# API metrics not available or not initialized
				pass

		except Exception as e:
			print(f"Error saving metrics: {e}")

	def save_now(self):
		"""Trigger an immediate save of all metrics"""
		self._save_all_metrics()


# Global metrics saver
_metrics_saver = MetricsPersistenceManager(interval=300)  # Save every 5 minutes
_metrics_saver.start()


class CursorWrapper:
	"""Wrapper around sqlite3.Cursor that adds metrics and logging"""

	def __init__(self, cursor: sqlite3.Cursor, logs):
		self._cursor = cursor
		self._logs = logs

	def execute(self, query: str, parameters = None):
		"""Execute a query with timing and logging"""
		start_time = time.time()
		error = None
		success = True

		# Handle None or empty parameters
		if parameters is None:
			parameters = ()
		elif not isinstance(parameters, (tuple, list)):
			parameters = (parameters,)

		try:
			# Log the query
			self._logs.debug(
				f"Executing SQL query",
				service="db",
				query=query[:200],  # Truncate long queries
				params=str(parameters)[:100] if parameters else None
			)

			# Execute with or without parameters
			if parameters:
				result = self._cursor.execute(query, parameters)
			else:
				result = self._cursor.execute(query)
			execution_time = time.time() - start_time

			# Log slow queries as warnings
			if execution_time > 0.1:  # 100ms threshold
				self._logs.warning(
					f"Slow query detected",
					service="db",
					query=query[:200],
					execution_time=f"{execution_time * 1000:.2f}ms"
				)

			return result

		except Exception as e:
			execution_time = time.time() - start_time
			success = False
			error = str(e)

			self._logs.error(
				f"Query execution failed",
				service="db",
				query=query[:200],
				error=error
			)
			raise

		finally:
			# Record metrics
			_db_metrics.record_individual_query(
				query=query,
				params=parameters,
				execution_time=execution_time,
				success=success,
				error=error
			)

	def executemany(self, query: str, seq_of_parameters):
		"""Execute a query multiple times with different parameters"""
		start_time = time.time()
		error = None
		success = True

		try:
			self._logs.debug(
				f"Executing batch SQL query",
				service="db",
				query=query[:200],
				batch_size=len(list(seq_of_parameters)) if hasattr(seq_of_parameters, '__len__') else 'unknown'
			)

			result = self._cursor.executemany(query, seq_of_parameters)
			execution_time = time.time() - start_time

			return result

		except Exception as e:
			execution_time = time.time() - start_time
			success = False
			error = str(e)

			self._logs.error(
				f"Batch query execution failed",
				service="db",
				query=query[:200],
				error=error
			)
			raise

		finally:
			# Record as single query for simplicity
			_db_metrics.record_individual_query(
				query=query,
				params=(),
				execution_time=execution_time,
				success=success,
				error=error
			)

	def executescript(self, script: str):
		"""Execute multiple SQL statements"""
		start_time = time.time()
		error = None
		success = True

		try:
			self._logs.debug(
				f"Executing SQL script",
				service="db",
				script=script[:200]
			)

			result = self._cursor.executescript(script)
			execution_time = time.time() - start_time

			return result

		except Exception as e:
			execution_time = time.time() - start_time
			success = False
			error = str(e)

			self._logs.error(
				f"Script execution failed",
				service="db",
				script=script[:200],
				error=error
			)
			raise

		finally:
			_db_metrics.record_individual_query(
				query=f"SCRIPT: {script[:100]}",
				params=(),
				execution_time=execution_time,
				success=success,
				error=error
			)

	# Delegate all other attributes to the underlying cursor
	def __getattr__(self, name):
		return getattr(self._cursor, name)


class _DB:
	def __init__(self, path, logs: Logs):
		self.path = path
		self.logs = logs
		self._start_time = None

	def __enter__(self) -> CursorWrapper:
		self._start_time = time.time()
		_db_metrics.increment_connections()
		self.logs.debug(f"Opening database connection", service="db", path=self.path)
		self._db = sqlite3.connect(self.path)
		self.cursor = self._db.cursor()
		# Return wrapped cursor with metrics and logging
		return CursorWrapper(self.cursor, self.logs)

	def __exit__(self, exc_type, exc_val, exc_tb):
		execution_time = time.time() - self._start_time if self._start_time else 0
		_db_metrics.decrement_connections()

		if exc_type:
			self.logs.error(f"Database transaction rolled back", service="db",
			               error=str(exc_val))
			self._db.rollback()
			_db_metrics.record_query(execution_time, success=False)
			return

		self.logs.debug("Database transaction committed", service="db")
		self._db.commit()
		_db_metrics.record_query(execution_time, success=True)


class Service(ABCService):
	def __init__(self, manager: Manager[ABCService]):
		self.manager = manager

		self._settings: Optional[Settings] = None
		self._migrations: Optional[Migrations] = None
		self._logs: Optional[Logs] = None

		self.logs.info(f"Initializing database service", service="db",
		              db_path=self.settings.db)

	def __call__(self):
		return _DB(self.settings.db, self.logs)

	@property
	def settings(self) -> Settings:
		if self._settings is None or not self._settings.ready:
			self._settings = self.manager.get[Settings]('settings')
		return self._settings

	@property
	def migrations(self):
		if self._migrations is None or not self._migrations.ready:
			from .migrations import Service as Migrations
			self._migrations = self.manager.get[Migrations]('settings')
		return self._migrations

	@property
	def logs(self):
		if self._logs is None or not self._logs.ready:
			from .logs import Service as Logs
			self._logs = self.manager.get[Logs]('logs')
		return self._logs

	@property
	def name(self) -> str:
		return "db"

	@property
	def ready(self) -> bool:
		return True

	def get_metrics(self) -> dict:
		"""Get database metrics statistics"""
		return _db_metrics.get_stats()

	def save_all_metrics(self):
		"""Save all metrics to disk immediately"""
		_metrics_saver.save_now()

def setup(manager: Manager[ABCService], /):
	require("settings")
	require("logs")
	require("cache")
	require("migrations")
	return Service(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)
