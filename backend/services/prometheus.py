from __future__ import annotations
from typing import TYPE_CHECKING, Any, cast, Optional
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup
	from .logs import Service as Logs

from flask import Flask, request, g
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, REGISTRY, CollectorRegistry
from prometheus_client.core import REGISTRY as DEFAULT_REGISTRY
import time

from ._base_service import ABCService
from ._manager import Manager
from .settings import Service as Settings

class NullPrometheus(ABCService):
	"""
	Null Prometheus service. Has all the same interface but dummy functions.
	"""


	def __init__(self):
		self._ready = True
		self.registry = CollectorRegistry()

	def _before_request(self):
		pass

	def _after_request(self, response):
		pass

	def _teardown_request(self, exception=None):
		pass

	def _handle_exception(self, error: Exception):
		pass

	def get_registry(self) -> CollectorRegistry:
		return self.registry

	def export_metrics(self) -> bytes:
		return generate_latest(self.registry)

	@property
	def name(self) -> str:
		return "prometheus"

	@property
	def ready(self) -> bool:
		return self._ready


class PrometheusMetricsService(NullPrometheus):
	"""
	Prometheus-based metrics service for Flask applications.

	Exposes metrics at /metrics endpoint in Prometheus format.
	Compatible with Prometheus, Grafana, and other monitoring tools.

	Metrics tracked:
	- flask_http_request_total: Total HTTP requests
	- flask_http_request_duration_seconds: Request duration histogram
	- flask_http_request_in_progress: Active requests gauge
	- flask_http_request_exceptions_total: Total exceptions
	- flask_app_info: Application metadata
	"""


	def __init__(self, logs: Optional[Logs] = None):
		self._ready = False
		self._app = None
		self._logs = logs

		# Use custom registry to avoid conflicts if multiple instances exist
		self.registry = CollectorRegistry()

		# Define Prometheus metrics
		self.request_count = Counter(
			'flask_http_request_total',
			'Total HTTP requests',
			['method', 'endpoint', 'status'],
			registry=self.registry
		)

		self.request_duration = Histogram(
			'flask_http_request_duration_seconds',
			'HTTP request duration in seconds',
			['method', 'endpoint'],
			buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
			registry=self.registry
		)

		self.requests_in_progress = Gauge(
			'flask_http_request_in_progress',
			'HTTP requests in progress',
			['method', 'endpoint'],
			registry=self.registry
		)

		self.exception_count = Counter(
			'flask_http_request_exceptions_total',
			'Total HTTP request exceptions',
			['method', 'endpoint', 'exception'],
			registry=self.registry
		)

		self.app_info = Info(
			'flask_app',
			'Flask application information',
			registry=self.registry
		)

	@property
	def logs(self) -> Optional[Logs]:
		return self._logs

	def initialize(self, app: Flask):
		"""
		Initialize Prometheus metrics tracking with Flask app.

		Args:
			app: Flask application instance
		"""
		if self._logs:
			self._logs.info("Initializing Prometheus metrics service", service="prometheus",
			               registry_type="custom")

		self._app = app

		# Set application metadata
		self.app_info.info({
			'version': '1.0.0',  # You can make this configurable
			'name': app.name
		})

		# Register before/after request hooks
		self._app.before_request(self._before_request)
		self._app.after_request(self._after_request)
		self._app.teardown_request(self._teardown_request)

		# Register exception handler
		self._app.errorhandler(Exception)(self._handle_exception)

		self._ready = True

		if self._logs:
			self._logs.info("Prometheus metrics service initialized successfully",
			               service="prometheus")

	def _before_request(self):
		"""Track request start time and increment in-progress counter."""
		g.start_time = time.time()

		endpoint = request.endpoint or 'unknown'
		method = request.method

		# Increment in-progress requests
		self.requests_in_progress.labels(method=method, endpoint=endpoint).inc()

	def _after_request(self, response):
		"""Track request completion and record metrics."""
		if hasattr(g, 'start_time'):
			duration = time.time() - g.start_time

			endpoint = request.endpoint or 'unknown'
			method = request.method
			status_code = response.status_code

			# Record duration
			self.request_duration.labels(
				method=method,
				endpoint=endpoint
			).observe(duration)

			# Increment request counter
			self.request_count.labels(
				method=method,
				endpoint=endpoint,
				status=status_code
			).inc()

		return response

	def _teardown_request(self, exception=None):
		"""Decrement in-progress requests counter."""
		endpoint = request.endpoint or 'unknown'
		method = request.method

		self.requests_in_progress.labels(method=method, endpoint=endpoint).dec()

	def _handle_exception(self, error: Exception):
		"""Track exceptions that occur during request processing."""
		endpoint = request.endpoint or 'unknown'
		method = request.method
		exception_type = type(error).__name__

		# Increment exception counter
		self.exception_count.labels(
			method=method,
			endpoint=endpoint,
			exception=exception_type
		).inc()

		# Re-raise the exception to let Flask handle it normally
		raise error

	def get_registry(self) -> CollectorRegistry:
		"""
		Get the Prometheus registry.

		Returns:
			CollectorRegistry instance containing all metrics
		"""
		return self.registry

	def export_metrics(self) -> bytes:
		"""
		Export metrics in Prometheus text format.

		Returns:
			Metrics data in Prometheus exposition format
		"""
		return generate_latest(self.registry)

	@property
	def name(self) -> str:
		return "prometheus"

	@property
	def ready(self) -> bool:
		return self._ready


class PrometheusMetricsServiceGlobal(NullPrometheus):
	"""
	Alternative Prometheus metrics service using the global REGISTRY.

	Use this if you want to use the default Prometheus registry instead of a custom one.
	Simpler but may have conflicts if multiple metric collectors are registered.
	"""

	def __init__(self, logs: Optional[Logs] = None):
		self._ready = False
		self._app = None
		self._logs = logs

		# Use global registry
		self.request_count = Counter(
			'flask_http_request_total',
			'Total HTTP requests',
			['method', 'endpoint', 'status']
		)

		self.request_duration = Histogram(
			'flask_http_request_duration_seconds',
			'HTTP request duration in seconds',
			['method', 'endpoint'],
			buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
		)

		self.requests_in_progress = Gauge(
			'flask_http_request_in_progress',
			'HTTP requests in progress',
			['method', 'endpoint']
		)

		self.exception_count = Counter(
			'flask_http_request_exceptions_total',
			'Total HTTP request exceptions',
			['method', 'endpoint', 'exception']
		)

		self.app_info = Info('flask_app', 'Flask application information')

	@property
	def logs(self) -> Optional[Logs]:
		return self._logs

	def initialize(self, app: Flask):
		"""
		Initialize Prometheus metrics tracking with Flask app.

		Args:
			app: Flask application instance
		"""
		if self._logs:
			self._logs.info("Initializing Prometheus metrics service", service="prometheus",
			               registry_type="global")

		self._app = app

		# Set application metadata
		self.app_info.info({
			'version': '1.0.0',
			'name': app.name
		})

		# Register hooks
		self._app.before_request(self._before_request)
		self._app.after_request(self._after_request)
		self._app.teardown_request(self._teardown_request)
		self._app.errorhandler(Exception)(self._handle_exception)

		self._ready = True

		if self._logs:
			self._logs.info("Prometheus metrics service initialized successfully",
			               service="prometheus")

	def _before_request(self):
		"""Track request start time and increment in-progress counter."""
		g.start_time = time.time()
		endpoint = request.endpoint or 'unknown'
		method = request.method
		self.requests_in_progress.labels(method=method, endpoint=endpoint).inc()

	def _after_request(self, response):
		"""Track request completion and record metrics."""
		if hasattr(g, 'start_time'):
			duration = time.time() - g.start_time
			endpoint = request.endpoint or 'unknown'
			method = request.method
			status_code = response.status_code

			self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
			self.request_count.labels(method=method, endpoint=endpoint, status=status_code).inc()

		return response

	def _teardown_request(self, exception=None):
		"""Decrement in-progress requests counter."""
		endpoint = request.endpoint or 'unknown'
		method = request.method
		self.requests_in_progress.labels(method=method, endpoint=endpoint).dec()

	def _handle_exception(self, error: Exception):
		"""Track exceptions."""
		endpoint = request.endpoint or 'unknown'
		method = request.method
		exception_type = type(error).__name__
		self.exception_count.labels(method=method, endpoint=endpoint, exception=exception_type).inc()
		raise error

	@property
	def name(self) -> str:
		return "prometheus"

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

	if settings.prometheus == 'global':
		return PrometheusMetricsServiceGlobal(logs=logs_service)
	elif settings.prometheus == 'custom':
		return PrometheusMetricsService(logs=logs_service)
	elif settings.prometheus == 'disabled':
		return NullPrometheus()
	raise ValueError("Invalid settings", settings.prometheus)


if TYPE_CHECKING:
	setup = validate_setup(setup)
