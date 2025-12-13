"""
Tasks API - Endpoints for managing background tasks.

Provides REST API for:
- Submitting tasks
- Checking task status
- Listing tasks
- Cancelling tasks
- Pausing/resuming task system
- Cleanup
"""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from ._base_api import ABCApi, describe, register
from ._manager import Manager
from flask import Blueprint, request, jsonify
from ..services.tasks import Service as TaskService
from ..plugins.models.tasks import Task


class TasksAPI(ABCApi):
	"""
	Task management API.

	Routes are under /v1/tasks
	"""

	def __init__(self, manager: Manager[ABCApi], parent: ABCApi):
		self.manager = manager
		self.parent = parent
		self.bp = self.create_blueprint("tasks", parent=parent, url_prefix="/tasks")
		self.tasks = self.manager.get[TaskService]('services.tasks')

		self.add_rules(self.bp)

	@register("/submit", methods=["POST"])
	@describe(
		"Submit a new task to the queue",
		"route",
		params={
			"task_name": {
				"type": "string",
				"required": True,
				"description": "Name of the registered task function",
				"in": "body",
			},
			"params": {
				"type": "object",
				"required": False,
				"description": "Parameters to pass to the task function",
				"in": "body",
			},
			"priority": {
				"type": "integer",
				"required": False,
				"description": "Task priority (higher = more important, default 0)",
				"in": "body",
			},
			"timeout": {
				"type": "number",
				"required": False,
				"description": "Task timeout in seconds (overrides default)",
				"in": "body",
			}
		},
		method="POST"
	)
	def submit_task(self):
		"""Submit a new task to the background queue."""
		data = request.get_json()

		if not data:
			return jsonify({"error": "No data provided"}), 400

		task_name = data.get("task_name")
		if not task_name:
			return jsonify({"error": "task_name is required"}), 400

		params = data.get("params", None)
		priority = data.get("priority", 0)
		timeout = data.get("timeout", None)

		try:
			task_id = self.tasks.submit(
				task_name=task_name,
				params=params,
				priority=priority,
				timeout=timeout
			)

			return jsonify({
				"task_id": task_id,
				"status": "queued",
				"priority": priority
			}), 201

		except KeyError as e:
			return jsonify({"error": str(e)}), 404
		except Exception as e:
			raise
			return jsonify({"error": f"Failed to submit task: {str(e)}"}), 500

	@register("/<int:task_id>", methods=["GET"])
	@describe(
		"Get task status and details",
		"route",
		params={
			"task_id": {
				"type": "integer",
				"required": True,
				"description": "Task ID",
				"in": "path",
			}
		},
		method="GET"
	)
	def get_task(self, task_id: int):
		"""Get status and details of a specific task."""
		task = self.tasks.get_status(task_id)

		if not task:
			return jsonify({"error": "Task not found"}), 404

		return jsonify(task), 200

	@register("/", methods=["GET"])
	@describe(
		"List all tasks with optional filtering",
		"route",
		params={
			"status": {
				"type": "string",
				"required": False,
				"description": "Filter by status (pending, running, completed, failed, timeout)",
				"in": "query",
			},
			"limit": {
				"type": "integer",
				"required": False,
				"description": "Maximum number of tasks to return",
				"in": "query",
			}
		},
		method="GET"
	)
	def list_tasks(self):
		"""List all tasks, optionally filtered by status."""
		status = request.args.get("status")
		limit = request.args.get("limit", type=int)

		# Get tasks from database
		if status:
			tasks = self.tasks.task_model.get_by_status(status)
		else:
			# Get all tasks (we'll need to add a get_all method or query directly)
			# For now, let's get pending, running, completed, failed, timeout
			all_tasks = []
			for s in [Task.TaskStatus.PENDING, Task.TaskStatus.RUNNING,
					  Task.TaskStatus.COMPLETED, Task.TaskStatus.FAILED,
					  Task.TaskStatus.TIMEOUT]:
				all_tasks.extend(self.tasks.task_model.get_by_status(s))
			tasks = all_tasks

		# Apply limit
		if limit:
			tasks = tasks[:limit]

		return jsonify({
			"tasks": tasks,
			"count": len(tasks)
		}), 200

	@register("/<int:task_id>/cancel", methods=["POST"])
	@describe(
		"Cancel a pending task",
		"route",
		params={
			"task_id": {
				"type": "integer",
				"required": True,
				"description": "Task ID to cancel",
				"in": "path",
			}
		},
		method="POST"
	)
	def cancel_task(self, task_id: int):
		"""Cancel a pending task (cannot cancel running tasks)."""
		success = self.tasks.cancel(task_id)

		if success:
			return jsonify({
				"message": "Task cancelled successfully",
				"task_id": task_id
			}), 200
		else:
			task = self.tasks.get_status(task_id)
			if not task:
				return jsonify({"error": "Task not found"}), 404
			else:
				return jsonify({
					"error": f"Cannot cancel task with status: {task['status']}",
					"task_id": task_id,
					"status": task['status']
				}), 400

	@register("/<int:task_id>", methods=["DELETE"])
	@describe(
		"Delete a task record",
		"route",
		params={
			"task_id": {
				"type": "integer",
				"required": True,
				"description": "Task ID to delete",
				"in": "path",
			}
		},
		method="DELETE"
	)
	def delete_task(self, task_id: int):
		"""Delete a task record from the database."""
		task = self.tasks.get_status(task_id)
		if not task:
			return jsonify({"error": "Task not found"}), 404

		self.tasks.task_model.delete(task_id)

		return jsonify({
			"message": "Task deleted successfully",
			"task_id": task_id
		}), 200

	@register("/system/pause", methods=["POST"])
	@describe(
		"Pause the task system",
		"route",
		method="POST"
	)
	def pause_system(self):
		"""
		Pause the task system.
		Running tasks continue, but no new tasks are picked up.
		"""
		self.tasks.pause()

		return jsonify({
			"message": "Task system paused",
			"paused": self.tasks.is_paused
		}), 200

	@register("/system/resume", methods=["POST"])
	@describe(
		"Resume the task system",
		"route",
		method="POST"
	)
	def resume_system(self):
		"""Resume the task system after pausing."""
		self.tasks.resume()

		return jsonify({
			"message": "Task system resumed",
			"paused": self.tasks.is_paused
		}), 200

	@register("/system/status", methods=["GET"])
	@describe(
		"Get task system status",
		"route",
		method="GET"
	)
	def system_status(self):
		"""Get current status of the task system."""
		running_tasks = self.tasks.get_running_tasks()

		return jsonify({
			"paused": self.tasks.is_paused,
			"workers_enabled": self.tasks.workers_enabled,
			"worker_count": self.tasks._worker_count,
			"running_tasks": len(running_tasks),
			"running_task_ids": [t['id'] for t in running_tasks]
		}), 200

	@register("/cleanup", methods=["POST"])
	@describe(
		"Clean up old completed/failed tasks",
		"route",
		params={
			"days": {
				"type": "integer",
				"required": False,
				"description": "Delete tasks older than this many days (default 7)",
				"in": "body",
			}
		},
		method="POST"
	)
	def cleanup_tasks(self):
		"""Delete old completed/failed/timeout tasks."""
		data = request.get_json() or {}
		days = data.get("days", 7)

		deleted_count = self.tasks.cleanup_old_tasks(days=days)

		return jsonify({
			"message": f"Cleaned up {deleted_count} old tasks",
			"deleted_count": deleted_count,
			"days": days
		}), 200

	@register("/running", methods=["GET"])
	@describe(
		"Get currently running tasks",
		"route",
		method="GET"
	)
	def running_tasks(self):
		"""Get list of currently running tasks."""
		running = self.tasks.get_running_tasks()

		return jsonify({
			"running_tasks": running,
			"count": len(running)
		}), 200

	@property
	def name(self) -> str:
		return "tasks"

	@property
	def blueprint(self) -> Blueprint:
		return self.bp


def setup(manager: Manager[ABCApi], /):
	"""Setup function - registers as child of v1 API"""
	parent = require('v1')
	return TasksAPI(manager, parent)

if TYPE_CHECKING:
	setup = validate_setup(setup)
