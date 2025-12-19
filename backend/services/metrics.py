from __future__ import annotations
from typing import TYPE_CHECKING, Any, cast, Optional
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup
	from .logs import Service as Logs

from collections import defaultdict
from datetime import datetime
from threading import Lock
from flask import Flask, g, request
import time
import json
import os

from ._base_service import ABCService
from ._manager import Manager
from .settings import Service as Settings


class NullMetrics(ABCService):
	"""
	Null Metrics service. Has all the same interface but dummy functions.
	"""

	def __init__(self):
		self._ready = True
		self._lock = Lock()
		self.start_time = datetime.now()

	def initialize(self, app: Flask):
		pass

	def _before_request(self):
		pass

	def _after_request(self, response):
		return response

	def _teardown_request(self, exception=None):
		pass

	def _handle_exception(self, error: Exception):
		raise error

	def _record_request(self, endpoint: str, method: str, duration: float, status_code: int):
		pass

	def get_stats(self) -> dict[str, Any]:
		return {
			'overview': {
				'total_requests': 0,
				'total_errors': 0,
				'active_requests': 0,
				'uptime_seconds': 0,
				'error_rate': 0
			},
			'endpoints': {},
			'error_types': {}
		}

	def reset_stats(self):
		pass

	def get_endpoint_stats(self, endpoint: str) -> dict[str, Any] | None:
		return None

	@property
	def name(self) -> str:
		return "metrics"

	@property
	def ready(self) -> bool:
		return self._ready


class MetricsService(NullMetrics):
	"""
	Middleware-based metrics service for tracking Flask application performance.

	Tracks:
	- Request counts per endpoint
	- Response times (avg, min, max, p95, p99)
	- Error rates and counts
	- Status code distribution
	- Active request count
	"""

	def __init__(self, logs: Optional[Logs] = None):
		self._lock = Lock()
		self._ready = False
		self._app = None
		self._logs = logs

		# Metrics storage
		self.request_count = defaultdict(int)  # {endpoint: count}
		self.response_times = defaultdict(list)  # {endpoint: [times]}
		self.error_count = defaultdict(int)  # {endpoint: count}
		self.status_codes = defaultdict(lambda: defaultdict(int))  # {endpoint: {status: count}}
		self.error_types = defaultdict(lambda: defaultdict(int))  # {endpoint: {exception_type: count}}
		self.active_requests = 0
		self.total_requests = 0
		self.total_errors = 0

		# Startup time
		self.start_time = datetime.now()

	@property
	def logs(self) -> Optional[Logs]:
		return self._logs

	def initialize(self, app: Flask):
		"""
		Initialize metrics tracking with Flask app.

		Args:
			app: Flask application instance
		"""
		if self._logs:
			self._logs.info("Initializing metrics service", service="metrics")

		# Load persisted metrics
		loaded = self.load_from_disk()
		if loaded and self._logs:
			self._logs.info("Loaded persisted API metrics", service="metrics")

		self._app = app

		# Register before/after request hooks
		self._app.before_request(self._before_request)
		self._app.after_request(self._after_request)
		self._app.teardown_request(self._teardown_request)

		# Register error handler
		self._app.errorhandler(Exception)(self._handle_exception)

		self._ready = True

		if self._logs:
			self._logs.info("Metrics service initialized successfully", service="metrics")

	def _before_request(self):
		"""Track request start time and increment active requests."""
		g.start_time = time.time()
		with self._lock:
			self.active_requests += 1

	def _after_request(self, response):
		"""Track request completion and record metrics."""
		if hasattr(g, 'start_time'):
			duration = time.time() - g.start_time

			endpoint = request.endpoint or 'unknown'
			method = request.method
			status_code = response.status_code

			self._record_request(
				endpoint=endpoint,
				method=method,
				duration=duration,
				status_code=status_code
			)

		return response

	def _teardown_request(self, exception=None):
		"""Decrement active requests counter."""
		with self._lock:
			self.active_requests = max(0, self.active_requests - 1)

	def _handle_exception(self, error: Exception):
		"""Track exceptions that occur during request processing."""
		endpoint = request.endpoint or 'unknown'
		exception_type = type(error).__name__

		with self._lock:
			self.error_types[endpoint][exception_type] += 1
			self.total_errors += 1

		# Re-raise the exception to let Flask handle it normally
		raise error

	def _record_request(self, endpoint: str, method: str, duration: float, status_code: int):
		"""Record metrics for a completed request."""
		key = f"{method}:{endpoint}"

		with self._lock:
			self.request_count[key] += 1
			self.response_times[key].append(duration)
			self.status_codes[key][status_code] += 1
			self.total_requests += 1

			if status_code >= 400:
				self.error_count[key] += 1

	def get_stats(self) -> dict[str, Any]:
		"""
		Get current metrics statistics.

		Returns:
			Dictionary containing all metrics data
		"""
		with self._lock:
			stats = {
				'overview': {
					'total_requests': self.total_requests,
					'total_errors': self.total_errors,
					'active_requests': self.active_requests,
					'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
					'error_rate': self.total_errors / self.total_requests if self.total_requests > 0 else 0
				},
				'endpoints': {}
			}

			for endpoint, times in self.response_times.items():
				if times:
					sorted_times = sorted(times)
					count = len(sorted_times)

					# Calculate percentiles
					p95_idx = int(count * 0.95)
					p99_idx = int(count * 0.99)

					stats['endpoints'][endpoint] = {
						'request_count': self.request_count[endpoint],
						'error_count': self.error_count[endpoint],
						'error_rate': self.error_count[endpoint] / self.request_count[endpoint],
						'response_time': {
							'avg': sum(times) / count,
							'min': min(times),
							'max': max(times),
							'p95': sorted_times[p95_idx] if p95_idx < count else sorted_times[-1],
							'p99': sorted_times[p99_idx] if p99_idx < count else sorted_times[-1]
						},
						'status_codes': dict(self.status_codes[endpoint])
					}

			# Add error types breakdown
			stats['error_types'] = {
				endpoint: dict(errors)
				for endpoint, errors in self.error_types.items()
			}

			return stats

	def reset_stats(self):
		"""Reset all metrics (useful for testing or periodic resets)."""
		with self._lock:
			self.request_count.clear()
			self.response_times.clear()
			self.error_count.clear()
			self.status_codes.clear()
			self.error_types.clear()
			self.total_requests = 0
			self.total_errors = 0
			self.start_time = datetime.now()

	def get_endpoint_stats(self, endpoint: str) -> dict[str, Any] | None:
		"""
		Get metrics for a specific endpoint.

		Args:
			endpoint: Endpoint to get stats for (e.g., "GET:/api/health")

		Returns:
			Dictionary with endpoint metrics or None if not found
		"""
		stats = self.get_stats()
		return stats['endpoints'].get(endpoint)

	def save_to_disk(self, filepath: str = "metrics/api_metrics.json"):
		"""Save metrics to disk"""
		with self._lock:
			# Create directory if it doesn't exist
			os.makedirs(os.path.dirname(filepath), exist_ok=True)

			# Convert defaultdicts to regular dicts for JSON serialization
			data = {
				'total_requests': self.total_requests,
				'total_errors': self.total_errors,
				'start_time': self.start_time.isoformat(),
				'request_count': dict(self.request_count),
				'response_times': {k: v for k, v in self.response_times.items()},
				'error_count': dict(self.error_count),
				'status_codes': {
					endpoint: dict(codes)
					for endpoint, codes in self.status_codes.items()
				},
				'error_types': {
					endpoint: dict(errors)
					for endpoint, errors in self.error_types.items()
				}
			}

			with open(filepath, 'w') as f:
				json.dump(data, f, indent=2)

	def load_from_disk(self, filepath: str = "metrics/api_metrics.json"):
		"""Load metrics from disk"""
		if not os.path.exists(filepath):
			return False

		try:
			with open(filepath, 'r') as f:
				data = json.load(f)

			with self._lock:
				self.total_requests = data.get('total_requests', 0)
				self.total_errors = data.get('total_errors', 0)

				# Load start time
				start_time_str = data.get('start_time')
				if start_time_str:
					self.start_time = datetime.fromisoformat(start_time_str)

				# Load request counts
				for endpoint, count in data.get('request_count', {}).items():
					self.request_count[endpoint] = count

				# Load response times
				for endpoint, times in data.get('response_times', {}).items():
					self.response_times[endpoint] = times

				# Load error counts
				for endpoint, count in data.get('error_count', {}).items():
					self.error_count[endpoint] = count

				# Load status codes
				for endpoint, codes in data.get('status_codes', {}).items():
					for code, count in codes.items():
						self.status_codes[endpoint][int(code)] = count

				# Load error types
				for endpoint, errors in data.get('error_types', {}).items():
					for error_type, count in errors.items():
						self.error_types[endpoint][error_type] = count

			return True
		except Exception as e:
			if self._logs:
				self._logs.error(f"Failed to load API metrics", service="metrics", error=str(e))
			return False

	@property
	def name(self) -> str:
		return "metrics"

	@property
	def ready(self) -> bool:
		return self._ready


def setup(manager: Manager[ABCService], /):
	from .logs import Service as Logs
	settings: Settings = cast(Settings, require('settings'))
	logs_service = None
	try:
		require('logs')
		logs_service = manager.get[Logs]('logs')
	except:
		pass

	if settings.metrics == 'enabled':
		return MetricsService(logs=logs_service)
	elif settings.metrics == 'disabled':
		return NullMetrics()
	raise ValueError("Invalid settings", settings.metrics)


if TYPE_CHECKING:
	setup = validate_setup(setup)
