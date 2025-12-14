from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from _injected import *

import json
import os
import traceback

from ._base_api import ABCApi, describe, register, cond
from ._manager import Manager
from flask import Blueprint, jsonify, request, current_app

from ..services import manager as services_manager
from ..plugins import manager as plugins_manager
from ..api import manager as api_manager

from ..services.prometheus import NullPrometheus
from ..services.metrics import NullMetrics
from ..services.settings import Service as Settings
from ..services.tasks import Service as Tasks
from ..services.cache import Service as Cache
from ..services.socketio import NullSocketIO

from ..plugins.auth import AuthUtils
from ..plugins.models.tasks import Task



class API(ABCApi):
	def __init__(self, manager: Manager[ABCApi]):
		self.manager = manager
		self.bp = self.create_blueprint("admin", url_prefix="/admin")

		# Get auth for authentication checks
		self.auth = AuthUtils()
		self.auth.manager = plugins_manager

		self.add_rules(self.bp)

	@register("/menu", methods=["GET"])
	@describe("Get admin menu structure", "route")
	@cond(lambda self: self.auth.require_admin())
	def get_menu(self):
		return jsonify({
			"sections": [
				{
					"id": "system",
					"label": "System",
					"items": [
						{"id": "overview", "label": "Overview", "icon": "dashboard"},
						{"id": "services", "label": "Services", "icon": "server"},
						{"id": "settings", "label": "Settings", "icon": "settings"}
					]
				},
				{
					"id": "data",
					"label": "Data Management",
					"items": [
						{"id": "database", "label": "Database", "icon": "database"},
						{"id": "cache", "label": "Cache", "icon": "cache"},
						{"id": "tasks", "label": "Tasks", "icon": "tasks"}
					]
				},
				{
					"id": "tools",
					"label": "Tools",
					"items": [
						{"id": "logs", "label": "Logs", "icon": "logs"},
						{"id": "metrics", "label": "Metrics", "icon": "chart"},
						{"id": "api-keys", "label": "API Keys", "icon": "key"}
					]
				}
			]
		})

	@register("/overview", methods=["GET"])
	@describe("Get system overview", "route")
	@cond(lambda self: self.auth.require_admin())
	def get_overview(self):
		services = []
		for service_name in services_manager.list_plugins():
			try:
				service = services_manager.get(service_name)
				services.append({"name": service.name, "ready": service.ready})
			except:
				services.append({"name": service_name, "ready": False})

		return jsonify({
			"title": "System Overview",
			"stats": [
				{"label": "Services Running", "value": sum(1 for s in services if s["ready"]), "total": len(services)},
				{"label": "APIs Loaded", "value": len(list(self.manager.list_plugins()))},
			],
			"services": services
		})

	@register("/services", methods=["GET"])
	@describe("Get services status", "route")
	@cond(lambda self: self.auth.require_admin())
	def get_services(self):
		services = []
		for service_name in services_manager.list_plugins():
			try:
				service = services_manager.get(service_name)
				services.append({
					"name": service.name,
					"ready": service.ready,
					"type": type(service).__name__,
					"module_path": service_name
				})
			except Exception as e:
				services.append({
					"name": service_name,
					"ready": False,
					"error": str(e),
					"module_path": service_name
				})

		return jsonify({
			"title": "Services Status",
			"description": "Manage and monitor backend services",
			"services": services,
			"actions": [
				{
					"id": "reload_all",
					"label": "Reload All Services",
					"endpoint": "/admin/reload",
					"method": "POST",
					"data": {"target": "services"}
				}
			]
		})

	@register("/tasks", methods=["GET", "POST"])
	@describe("Get tasks or create new task", "route")
	@cond(lambda self: self.auth.require_admin())
	def manage_tasks(self):
		tasks_service = services_manager.get[Tasks]("tasks")

		if request.method == "POST":
			data = request.get_json()
			if not data or not data.get("task_name"):
				return jsonify({"error": "task_name is required"}), 400

			try:
				task_id = tasks_service.submit(
					task_name=data["task_name"],
					params=data.get("params", {}),
					priority=data.get("priority", 0),
					timeout=data.get("timeout")
				)
				return jsonify({"task_id": task_id, "message": "Task created successfully"})
			except KeyError as e:
				return jsonify({"error": str(e)}), 404
			except Exception as e:
				return jsonify({"error": str(e)}), 500

		try:
			running = tasks_service.get_running_tasks()

			all_tasks = []
			for status in [Task.TaskStatus.PENDING, Task.TaskStatus.RUNNING,
						   Task.TaskStatus.COMPLETED, Task.TaskStatus.FAILED,
						   Task.TaskStatus.TIMEOUT]:
				all_tasks.extend(tasks_service.task_model.get_by_status(status))

			all_tasks.sort(key=lambda x: x.get('created_at', 0), reverse=True)
			all_tasks = all_tasks[:100]

			return jsonify({
				"title": "Tasks System",
				"description": "Background task execution management",
				"status": {
					"workers_enabled": tasks_service.workers_enabled,
					"worker_count": tasks_service._worker_count,
					"paused": tasks_service.is_paused,
					"running_tasks": len(running)
				},
				"tasks": all_tasks,
				"registered_tasks": list(tasks_service._registry.keys()),
				"actions": [
					{"id": "pause", "label": "Pause System", "method": "POST", "endpoint": "/api/v1/tasks/system/pause"},
					{"id": "resume", "label": "Resume System", "method": "POST", "endpoint": "/api/v1/tasks/system/resume"},
					{"id": "cleanup", "label": "Cleanup Old Tasks", "method": "POST", "endpoint": "/api/v1/tasks/cleanup"}
				]
			})
		except Exception as e:
			return jsonify({"title": "Tasks System", "error": f"Failed to get tasks: {str(e)}"})

	@register("/tasks/<int:task_id>/requeue", methods=["POST"])
	@describe("Requeue a pending task", "route")
	@cond(lambda self, **kwargs: self.auth.require_admin())
	def requeue_task(self, task_id: int):
		"""Requeue a pending task that's not in the queue (e.g., after restart)"""
		try:
			tasks_service = services_manager.get[Tasks]("tasks")
			success = tasks_service.requeue(task_id)

			if success:
				# Emit Socket.IO event to refresh tasks page
				socketio = services_manager.get[NullSocketIO]("socketio")
				socketio.broadcast('refresh_page', {'page': 'tasks'})

				return jsonify({"message": f"Task {task_id} requeued successfully"})
			else:
				task = tasks_service.get_status(task_id)
				if not task:
					return jsonify({"error": "Task not found"}), 404
				elif task['status'] != Task.TaskStatus.PENDING:
					return jsonify({"error": f"Task is {task['status']}, can only requeue PENDING tasks"}), 400
				else:
					return jsonify({"error": "Task function is not registered"}), 400
		except Exception as e:
			traceback.print_exc()
			return jsonify({"error": f"Failed to requeue task: {str(e)}"}), 500

	@register("/settings", methods=["GET", "POST"])
	@describe("Get or update settings", "route")
	@cond(lambda self: self.auth.require_admin())
	def manage_settings(self):
		settings_service = services_manager.get[Settings]("settings")

		if request.method == "POST":
			try:
				updates = request.get_json()
				if not updates:
					return jsonify({"error": "No updates provided"}), 400

				with open("settings.json", 'r') as f:
					current_settings = json.load(f)

				current_settings.update(updates)

				with open("settings.json", 'w') as f:
					json.dump(current_settings, f, indent=2)

				return jsonify({"message": "Settings updated. Restart required.", "updated": list(updates.keys())})
			except Exception as e:
				return jsonify({"error": f"Failed to update: {str(e)}"}), 500

		schema = Settings.get_settings_schema()
		with open("settings.json", 'r') as f:
			current = json.load(f)

		return jsonify({
			"title": "Settings",
			"description": "Application configuration (restart required after changes)",
			"schema": schema,
			"current": current
		})

	@register("/database", methods=["GET"])
	@describe("Get database info", "route")
	@cond(lambda self: self.auth.require_admin())
	def get_database(self):
		settings = services_manager.get[Settings]("settings")
		db_path = settings.db

		file_size = 0
		if os.path.exists(db_path):
			file_size = os.path.getsize(db_path)

		return jsonify({
			"title": "Database",
			"description": "Database management and information",
			"info": {
				"path": db_path,
				"type": "SQLite3",
				"size": f"{file_size / 1024:.2f} KB" if file_size else "0 KB"
			},
			"actions": [
				{"id": "vacuum", "label": "Vacuum Database", "description": "Optimize database storage"},
				{"id": "backup", "label": "Create Backup", "description": "Create database backup"}
			]
		})

	@register("/cache", methods=["GET"])
	@describe("Get cache info", "route")
	@cond(lambda self: self.auth.require_admin())
	def get_cache(self):
		try:
			cache = services_manager.get[Cache]("cache")
			return jsonify({
				"title": "Cache",
				"description": "Redis cache management",
				"status": {
					"ready": cache.ready,
					"type": type(cache).__name__
				}
			})
		except Exception as e:
			return jsonify({"title": "Cache", "error": f"Failed to get cache info: {str(e)}"})

	@register("/logs", methods=["GET"])
	@describe("Get logs", "route")
	@cond(lambda self: self.auth.require_admin())
	def get_logs(self):
		import logging
		from datetime import datetime

		# Get query parameters
		limit = int(request.args.get('limit', 100))
		level = request.args.get('level', 'DEBUG').upper()

		# Collect recent logs from all loggers
		logs = []

		# Get root logger and all child loggers
		root_logger = logging.getLogger()
		all_loggers = [root_logger] + [logging.getLogger(name) for name in logging.root.manager.loggerDict]

		# Collect log records (this is a simplified approach - in production you'd use a log file or handler)
		# For now, we'll create sample logs showing the system state
		logs.append({
			"timestamp": datetime.now().isoformat(),
			"level": "INFO",
			"logger": "system",
			"message": f"Application running with {len(list(services_manager.list_plugins()))} services loaded"
		})

		logs.append({
			"timestamp": datetime.now().isoformat(),
			"level": "INFO",
			"logger": "system",
			"message": f"API modules: {', '.join(list(api_manager.list_plugins()))}"
		})

		# Get task system status
		try:
			tasks_service = services_manager.get[Tasks]("tasks")
			running = tasks_service.get_running_tasks()
			logs.append({
				"timestamp": datetime.now().isoformat(),
				"level": "INFO",
				"logger": "tasks",
				"message": f"Task system active: {tasks_service.workers_enabled}, running tasks: {len(running)}"
			})
		except Exception as e:
			logs.append({
				"timestamp": datetime.now().isoformat(),
				"level": "WARNING",
				"logger": "tasks",
				"message": f"Task service error: {str(e)}"
			})

		# Get metrics status
		try:
			metrics_service = services_manager.get[NullMetrics]("metrics")
			if metrics_service.ready:
				stats = metrics_service.get_stats()
				logs.append({
					"timestamp": datetime.now().isoformat(),
					"level": "INFO",
					"logger": "metrics",
					"message": f"Total requests: {stats['overview']['total_requests']}, errors: {stats['overview']['total_errors']}"
				})
		except Exception as e:
			logs.append({
				"timestamp": datetime.now().isoformat(),
				"level": "WARNING",
				"logger": "metrics",
				"message": f"Metrics service error: {str(e)}"
			})

		return jsonify({
			"title": "Logs",
			"description": "Application logs and system status",
			"logs": logs[:limit],
			"filters": {
				"level": level,
				"limit": limit
			}
		})

	@register("/metrics", methods=["GET"])
	@describe("Get metrics", "route")
	@cond(lambda self: self.auth.require_admin())
	def get_metrics(self):
		try:
			metrics_service = services_manager.get[NullMetrics]("metrics")

			if not metrics_service.ready:
				return jsonify({
					"title": "Metrics",
					"description": "Application metrics and monitoring",
					"error": "Metrics service not ready"
				})

			stats = metrics_service.get_stats()

			# Format uptime
			uptime_seconds = stats['overview']['uptime_seconds']
			uptime_hours = uptime_seconds / 3600
			uptime_days = uptime_hours / 24

			if uptime_days >= 1:
				uptime_formatted = f"{uptime_days:.1f} days"
			elif uptime_hours >= 1:
				uptime_formatted = f"{uptime_hours:.1f} hours"
			else:
				uptime_formatted = f"{uptime_seconds:.0f} seconds"

			# Sort endpoints by request count
			endpoints_list = []
			for endpoint, data in stats['endpoints'].items():
				endpoints_list.append({
					'endpoint': endpoint,
					'request_count': data['request_count'],
					'error_count': data['error_count'],
					'error_rate': f"{data['error_rate'] * 100:.2f}%",
					'avg_response_time': f"{data['response_time']['avg'] * 1000:.2f}ms",
					'p95_response_time': f"{data['response_time']['p95'] * 1000:.2f}ms",
					'p99_response_time': f"{data['response_time']['p99'] * 1000:.2f}ms",
					'status_codes': data['status_codes']
				})

			endpoints_list.sort(key=lambda x: x['request_count'], reverse=True)

			return jsonify({
				"title": "Metrics",
				"description": "Application metrics and monitoring",
				"overview": {
					"total_requests": stats['overview']['total_requests'],
					"total_errors": stats['overview']['total_errors'],
					"active_requests": stats['overview']['active_requests'],
					"uptime": uptime_formatted,
					"error_rate": f"{stats['overview']['error_rate'] * 100:.2f}%"
				},
				"endpoints": endpoints_list,
				"error_types": stats.get('error_types', {})
			})
		except Exception as e:
			traceback.print_exc()
			return jsonify({"title": "Metrics", "error": f"Failed to get metrics: {str(e)}"})

	@register("/api-keys", methods=["GET", "POST"])
	@describe("Get or create API keys", "route")
	@cond(lambda self: self.auth.require_admin())
	def manage_api_keys(self):
		auth_plugin = plugins_manager.get('auth')

		if request.method == "POST":
			data = request.get_json()
			level = data.get("level", 0)
			expire = data.get("expire")

			try:
				# Create the API key
				api_key = auth_plugin.create_apikey(level=level, expire=expire)

				return jsonify({
					"message": "API key created successfully",
					"key": api_key,
					"level": level,
					"expire": expire
				}), 201
			except Exception as e:
				traceback.print_exc()
				return jsonify({"error": f"Failed to create API key: {str(e)}"}), 500

		# GET request - list all API keys
		try:
			keys = auth_plugin.list_apikeys(limit=1000)

			# Convert to dict format, excluding the actual key value for security
			keys_data = []
			for key in keys:
				keys_data.append({
					"id": key.id,
					"key_preview": f"{key.key[:8]}...{key.key[-4:]}" if len(key.key) > 12 else "***",
					"level": key.level,
					"expire": key.expire,
					"created_at": key.created_at,
					"last_used": key.last_used
				})

			return jsonify({
				"title": "API Keys",
				"description": "Manage API keys for programmatic access",
				"keys": keys_data,
				"levels": [
					{"value": 0, "label": "User", "description": "Standard user access"},
					{"value": 1, "label": "Admin", "description": "Full administrative access"}
				]
			})
		except Exception as e:
			traceback.print_exc()
			return jsonify({"title": "API Keys", "error": f"Failed to load API keys: {str(e)}"})

	@register("/api-keys/<int:key_id>", methods=["DELETE"])
	@describe("Delete an API key", "route")
	@cond(lambda self, **kwargs: self.auth.require_admin())
	def delete_api_key(self, key_id: int):
		auth_plugin = plugins_manager.get('auth')

		try:
			result = auth_plugin.delete_apikey(key_id)

			if isinstance(result, auth_plugin.OperationSuccess):
				return jsonify({"message": f"API key {key_id} deleted successfully"})
			else:
				return jsonify({"error": result.error}), 404
		except Exception as e:
			traceback.print_exc()
			return jsonify({"error": f"Failed to delete API key: {str(e)}"}), 500

	@register("/reload", methods=["POST"])
	@describe("Reload system modules", "route")
	@cond(lambda self: self.auth.require_admin())
	def reload_system(self):
		"""
		Reload system modules based on the 'target' parameter.

		Accepts JSON body with:
		- target: "all" | "services" | "plugins" | "apis" | specific module name
		"""
		from ..app import reload_all
		from ..services._manager import reload_all_services
		from ..plugins._manager import reload_all_plugins
		from ..api._manager import reload_all_apis, unregister_blueprints

		data = request.get_json() or {}
		target = data.get("target", "all")

		try:
			socketio = services_manager.get[NullSocketIO]("socketio")

			if target == "all":
				results = reload_all()
				socketio.broadcast('refresh_page', {'page': 'services'})
				socketio.broadcast('refresh_page', {'page': 'overview'})
				return jsonify({
					"message": "Full system reload completed",
					"results": {
						"services": len(results['services']),
						"plugins": len(results['plugins']),
						"apis": len(results['apis'])
					}
				})
			elif target == "services":
				results = reload_all_services()
				socketio.broadcast('refresh_page', {'page': 'services'})
				return jsonify({
					"message": f"Reloaded {len(results)} service(s)",
					"reloaded": list(results.keys())
				})
			elif target == "plugins":
				results = reload_all_plugins()
				return jsonify({
					"message": f"Reloaded {len(results)} plugin(s)",
					"reloaded": list(results.keys())
				})
			elif target == "apis":
				results = reload_all_apis(current_app)
				return jsonify({
					"message": f"Reloaded {len(results)} API(s)",
					"reloaded": list(results.keys())
				})
			else:
				# Try to reload a specific module
				# First check which manager it belongs to
				reloaded = False
				manager_name = None

				if target in services_manager._modules_specs:
					services_manager.reload(target)
					reloaded = True
					manager_name = "services"
				elif target in plugins_manager._modules_specs:
					plugins_manager.reload(target)
					reloaded = True
					manager_name = "plugins"
				elif target in api_manager._modules_specs:
					# For APIs, need to handle blueprints
					api_instance = api_manager._modules.get(target)
					if api_instance and hasattr(api_instance, 'blueprint'):
						unregister_blueprints(current_app, api_instance.blueprint.name)

					api_manager.reload(target)

					# Re-register blueprint
					new_instance = api_manager.get(target)
					if hasattr(new_instance, 'blueprint'):
						current_app.register_blueprint(new_instance.blueprint)

					reloaded = True
					manager_name = "apis"

				if reloaded:
					if manager_name == "services":
						socketio.broadcast('refresh_page', {'page': 'services'})
					return jsonify({
						"message": f"Reloaded {target} from {manager_name}",
						"target": target,
						"manager": manager_name
					})
				else:
					return jsonify({"error": f"Module '{target}' not found"}), 404

		except Exception as e:
			traceback.print_exc()
			return jsonify({"error": f"Reload failed: {str(e)}"}), 500

	@property
	def name(self) -> str:
		return "admin"

	@property
	def blueprint(self) -> Blueprint:
		return self.bp


def setup(manager: Manager[ABCApi], /):
	return API(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)
