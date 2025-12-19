from typing import Any, Dict
from abc import ABC, abstractmethod
from collections import defaultdict
from threading import Lock
import time
import json
import os
from .._base_plugin import ABCPlugin
from .._manager import Manager
from ...services.db import Service as DB


# Global metrics storage for model operations
class ModelMetrics:
	"""Thread-safe model metrics collector"""
	def __init__(self):
		self.lock = Lock()
		# Per-model operation counts: {model_name: {operation: count}}
		self.operation_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
		# Per-model operation times: {model_name: {operation: [times]}}
		self.operation_times: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))
		# Per-model error counts: {model_name: {operation: count}}
		self.operation_errors: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

	def record_operation(self, model_name: str, operation: str, execution_time: float, success: bool = True):
		"""Record a model operation"""
		with self.lock:
			self.operation_counts[model_name][operation] += 1
			if success:
				self.operation_times[model_name][operation].append(execution_time)
				# Keep only last 100 operations per model/operation
				if len(self.operation_times[model_name][operation]) > 100:
					self.operation_times[model_name][operation].pop(0)
			else:
				self.operation_errors[model_name][operation] += 1

	def get_stats(self) -> Dict[str, Any]:
		"""Get current metrics stats"""
		with self.lock:
			stats = {}
			for model_name in self.operation_counts:
				model_stats = {
					'operations': dict(self.operation_counts[model_name]),
					'errors': dict(self.operation_errors[model_name]),
					'avg_times': {}
				}

				# Calculate average times per operation
				for operation, times in self.operation_times[model_name].items():
					if times:
						model_stats['avg_times'][operation] = sum(times) / len(times)
					else:
						model_stats['avg_times'][operation] = 0.0

				stats[model_name] = model_stats

			return stats

	def get_total_operations(self) -> int:
		"""Get total number of operations across all models"""
		with self.lock:
			total = 0
			for model_counts in self.operation_counts.values():
				total += sum(model_counts.values())
			return total

	def get_total_errors(self) -> int:
		"""Get total number of errors across all models"""
		with self.lock:
			total = 0
			for model_errors in self.operation_errors.values():
				total += sum(model_errors.values())
			return total

	def save_to_disk(self, filepath: str = "metrics/model_metrics.json"):
		"""Save metrics to disk"""
		with self.lock:
			# Create directory if it doesn't exist
			os.makedirs(os.path.dirname(filepath), exist_ok=True)

			# Convert defaultdicts to regular dicts for JSON serialization
			data = {
				'operation_counts': {
					model: dict(ops) for model, ops in self.operation_counts.items()
				},
				'operation_times': {
					model: {op: times for op, times in ops.items()}
					for model, ops in self.operation_times.items()
				},
				'operation_errors': {
					model: dict(errors) for model, errors in self.operation_errors.items()
				}
			}

			with open(filepath, 'w') as f:
				json.dump(data, f, indent=2)

	def load_from_disk(self, filepath: str = "metrics/model_metrics.json"):
		"""Load metrics from disk"""
		if not os.path.exists(filepath):
			return False

		try:
			with open(filepath, 'r') as f:
				data = json.load(f)

			with self.lock:
				# Load operation counts
				for model, ops in data.get('operation_counts', {}).items():
					for op, count in ops.items():
						self.operation_counts[model][op] = count

				# Load operation times
				for model, ops in data.get('operation_times', {}).items():
					for op, times in ops.items():
						self.operation_times[model][op] = times

				# Load operation errors
				for model, errors in data.get('operation_errors', {}).items():
					for op, count in errors.items():
						self.operation_errors[model][op] = count

			return True
		except Exception as e:
			print(f"Failed to load model metrics: {e}")
			return False


# Global instance
_model_metrics = ModelMetrics()
# Load persisted metrics on startup
_model_metrics.load_from_disk()

class ABCModel(ABCPlugin, ABC):
	def __init__(self, manager: Manager[ABCPlugin]):
		self._db = manager.get[DB]('services.db')
		self.ensure()

	@property
	def db(self) -> DB:
		return self._db

	def _track_operation(self, operation: str):
		"""
		Context manager to track model operations with timing and error handling.

		Usage:
			with self._track_operation('create'):
				# perform operation
				pass
		"""
		class OperationTracker:
			def __init__(tracker_self, model_name: str, op: str):
				tracker_self.model_name = model_name
				tracker_self.operation = op
				tracker_self.start_time = None

			def __enter__(tracker_self):
				tracker_self.start_time = time.time()
				return tracker_self

			def __exit__(tracker_self, exc_type, exc_val, exc_tb):
				execution_time = time.time() - tracker_self.start_time if tracker_self.start_time else 0
				success = exc_type is None
				_model_metrics.record_operation(tracker_self.model_name, tracker_self.operation, execution_time, success)
				return False  # Don't suppress exceptions

		return OperationTracker(self.name, operation)

	@staticmethod
	def get_metrics() -> Dict[str, Any]:
		"""Get model metrics statistics"""
		return _model_metrics.get_stats()

	@staticmethod
	def get_total_operations() -> int:
		"""Get total operations across all models"""
		return _model_metrics.get_total_operations()

	@staticmethod
	def get_total_errors() -> int:
		"""Get total errors across all models"""
		return _model_metrics.get_total_errors()

	@abstractmethod
	def ensure(self, *args, **kwargs) -> Any: ...
	@abstractmethod
	def create(self, *args, **kwargs) -> Any: ...
	@abstractmethod
	def delete(self, *args, **kwargs) -> bool: ...
	@abstractmethod
	def update(self, *args, **kwargs) -> Any: ...

	# Admin interface methods
	@abstractmethod
	def get_all(self, limit: int = 50, offset: int = 0) -> list[dict]:
		"""
		Get all records with pagination.

		Args:
			limit: Maximum number of records to return
			offset: Number of records to skip

		Returns:
			List of record dictionaries
		"""
		...

	@abstractmethod
	def get_count(self) -> int:
		"""
		Get total count of records in the model.

		Returns:
			Total number of records
		"""
		...

	@abstractmethod
	def get_column_definitions(self) -> list[dict]:
		"""
		Get column definitions for admin UI display.

		Returns:
			List of column definition dictionaries with keys:
			- key: Column identifier
			- label: Display name
			- type: Data type (text, number, date, etc.)
			- sortable: Whether column is sortable
			- truncate: Whether to truncate long text
		"""
		...
