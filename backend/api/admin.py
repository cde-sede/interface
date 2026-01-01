from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from _injected import *

import json
import os
import traceback
import logging
import re
import ast
from datetime import datetime, timezone

from ._base_api import ABCApi, describe, register, cond
from ._manager import Manager
from flask import Blueprint, jsonify, request, current_app

from ..services import ABCService
from ..plugins import ABCPlugin

from ..services.prometheus import NullPrometheus
from ..services.metrics import NullMetrics
from ..services.settings import Service as Settings
from ..services.tasks import Service as Tasks
from ..services.cache import Service as Cache
from ..services.socketio import NullSocketIO
from ..services.db import Service as DB
from ..services.logs import Service as Logs

from ..plugins.auth import AuthUtils, Plugin as Auth
from ..plugins.models.tasks import Task
from ..plugins.models.webhook import Webhook
from ..plugins.model import Plugin as Models

from ..plugins.models._model import ABCModel



from ..services._manager import reload_all_services
from ..plugins._manager import reload_all_plugins
from ..api._manager import reload_all_apis, unregister_blueprints, reload_all

from ._dsl_builder import *
from ._dsl_types import *


def SanitizeLogs(s: str) -> str:
	"""Remove ANSI escape codes and non-printable characters from log strings"""
	return ''.join(c for c in re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', s) if c.isprintable())


class API(ABCApi):
	def __init__(self, manager: Manager[ABCApi]):
		self.manager = manager
		self.bp = self.create_blueprint("admin", url_prefix="/admin")

		# Get auth for authentication checks
		self.auth = AuthUtils()
		self.auth.manager = self.manager.get[Manager[ABCPlugin]]("plugins")

		self._logs = None
		self._models = None

		self.add_rules(self.bp)
		self._register_socketio_handlers()

	@property
	def models(self) -> Models:
		if self._models is None:
			self._models = self.manager.get[Models]('plugins.models')
		return self._models

	@property
	def isroot(self) -> bool:
		return True

	@property
	def logs(self) -> Logs:
		"""Get logs service"""
		if self._logs is None:
			services_manager = self.manager.get[Manager[ABCService]]("services")
			self._logs = services_manager.get[Logs]("logs")
		return self._logs

	def _register_socketio_handlers(self):
		"""Register Socket.IO event handlers for admin page auto-reload."""
		from ..services.socketio import Service as SocketIOService
		from flask_socketio import join_room, leave_room
		from flask import request as flask_request

		services_manager = self.manager.get[Manager[ABCService]]("services")
		socketio = services_manager.get[SocketIOService]("socketio")

		@socketio.on('join_page')
		def handle_join_page(data):
			"""Handle client joining a page room for auto-reload."""
			try:
				page = data.get('page')
				if not page:
					self.logs.warning("Join page request missing page name", service="admin",
					                session_id=flask_request.sid)
					return

				session_id = flask_request.sid
				room_name = f"page_{page}"

				join_room(room_name)

				# Track current page in session
				if hasattr(socketio, '_sessions_lock') and hasattr(socketio, '_sessions'):
					with socketio._sessions_lock:
						if session_id in socketio._sessions:
							socketio._sessions[session_id]['current_page'] = page

				self.logs.debug("Client joined page room", service="admin",
				              session_id=session_id, page=page, room=room_name)
			except Exception as e:
				self.logs.error("Error joining page room", service="admin",
				              error=str(e), session_id=flask_request.sid)

		@socketio.on('leave_page')
		def handle_leave_page(data):
			"""Handle client leaving a page room."""
			try:
				page = data.get('page')
				if not page:
					self.logs.warning("Leave page request missing page name", service="admin",
					                session_id=flask_request.sid)
					return

				session_id = flask_request.sid
				room_name = f"page_{page}"

				leave_room(room_name)

				# Clear current page from session
				if hasattr(socketio, '_sessions_lock') and hasattr(socketio, '_sessions'):
					with socketio._sessions_lock:
						if session_id in socketio._sessions:
							socketio._sessions[session_id].pop('current_page', None)

				self.logs.debug("Client left page room", service="admin",
				              session_id=session_id, page=page, room=room_name)
			except Exception as e:
				self.logs.error("Error leaving page room", service="admin",
				              error=str(e), session_id=flask_request.sid)

	def _get_status_description(self, status_code: int) -> str:
		"""Get human-readable description for HTTP status code"""
		descriptions = {
			200: "OK",
			201: "Created",
			204: "No Content",
			301: "Moved Permanently",
			302: "Found",
			304: "Not Modified",
			400: "Bad Request",
			401: "Unauthorized",
			403: "Forbidden",
			404: "Not Found",
			405: "Method Not Allowed",
			409: "Conflict",
			422: "Unprocessable Entity",
			429: "Too Many Requests",
			500: "Internal Server Error",
			502: "Bad Gateway",
			503: "Service Unavailable",
			504: "Gateway Timeout"
		}
		return descriptions.get(status_code, "Unknown")

	@register("/menu", methods=["GET"])
	@describe("Get admin menu structure", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_menu(self):
		return jsonify({
			"sections": [
				{
					"id": "system",
					"label": "System",
					"items": [
						{"id": "overview", "label": "Overview", "icon": "dashboard"},
						{"id": "services", "label": "Services", "icon": "server"},
						{"id": "settings", "label": "Settings", "icon": "settings"},
					]
				},
				{
					"id": "data",
					"label": "Data Management",
					"items": [
						{"id": "database", "label": "Database", "icon": "database"},
						{"id": "cache", "label": "Cache", "icon": "cache"},
						{"id": "tasks", "label": "Tasks", "icon": "tasks"},
						{"id": "webhooks", "label": "Webooks", "icon": "webhooks"},
					]
				},
				{
					"id": "tools",
					"label": "Tools",
					"items": [
						{"id": "logs", "label": "Logs", "icon": "logs"},
						{"id": "metrics", "label": "Metrics", "icon": "chart"},
						{"id": "api-keys", "label": "API Keys", "icon": "key"},
					]
				},
				{
					"id": "development",
					"label": "Development",
					"items": [
						{"id": "dsl-showcase", "label": "DSL Showcase", "icon": "zap"},
					]
				}
			]
		})

	@register("/overview", methods=["GET"])
	@describe("Get system overview", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_overview(self):
		services_manager = self.manager.get[Manager[ABCService]]("services")
		services = []
		for service_name in services_manager.list_plugins():
			try:
				service = services_manager.get[ABCService](service_name)
				services.append({"name": service.name, "ready": service.ready})
			except:
				services.append({"name": service_name, "ready": False})
		return jsonify(
			PageBuilder(
				title="System Overview",
				description="Monitor system health and status"
			).add_section(
				SectionBuilder()
				.add_stats_cards([
					create_stat_card(
						"Services Running",
						sum(1 for s in services if s["ready"]),
						total=len(services)
					),
					create_stat_card(
						"APIs Loaded",
						len(list(self.manager.list_plugins()))
					)
				], columns=2)
			).add_section(
				SectionBuilder("Services")
				.add_table(
					TableBuilder(services)
					.add_column("name", "Service", type="code")\
					.add_status_column(
						"ready",
						"Status",
						config={
							"true": {"label": "Ready", "variant": "success"},
							"false": {"label": "Not Ready", "variant": "error"}
						}
					)
				)
			).build()
		)

	@register("/services", methods=["GET"])
	@describe("Get services status", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_services(self):
		services_manager = self.manager.get[Manager[ABCService]]("services")
		services = []
		for service_name in services_manager.list_plugins():
			try:
				service = services_manager.get[ABCService](service_name)
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
		# Build DSL
		return jsonify(
			PageBuilder(
				title="Services Status",
				description="Manage and monitor backend services"
			).add_section(SectionBuilder()
				.add_table(
					TableBuilder(services)
					.add_column("name", "Name", type="code")
					.add_column("type", "Type")
					.add_status_column(
						"ready",
						"Status",
						config={
							"true": {"label": "Ready", "variant": "success"},
							"false": {"label": "Not Ready", "variant": "error"}
						}
					)

					.add_header_action(
						"reload_all",
						"Reload All Services",
						ActionBuilder().api_call(
							"/admin/reload",
							method="POST",
							body={"target": ValueRefBuilder.literal("services")}
						).on_success(
							message="Services reloaded successfully",
							action=ActionBuilder().refresh()
						),
						confirm_message="Reload all services? This may cause temporary disruption."
					)

					.add_row_action(
						"reload",
						"Reload",
						ActionBuilder().api_call(
							"/admin/reload",
							method="POST",
							body={"target": ValueRefBuilder.field("row", "module_path")}
						).on_success(
							message="Service reloaded",
							action=ActionBuilder().refresh()
						),
						confirm_message=ValueRefBuilder.computed(
							"Reload service {name}?",
							name=ValueRefBuilder.field("row", "name")
						)
					)
				)
			).set_realtime(
				socket_events=[
					SocketEventHandler(
						event="refresh_page",
						handler="refresh-page"
					),
					SocketEventHandler(
						event="task_update",
						handler="refresh-page"
					),
				]
			).build()
		)

	@register("/tasks", methods=["GET", "POST"])
	@describe("Get tasks or create new task", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def manage_tasks(self):
		tasks_service = self.manager.get[Tasks]("services.tasks")
		socketio = self.manager.get[NullSocketIO]("services.socketio")

		if request.method == "POST":
			data = request.get_json()
			if not data or not data.get("task_name"):
				return jsonify({"error": "task_name is required"}), 400

			# Check if task system is paused
			if tasks_service.is_paused:
				return jsonify({"error": "Task system is paused. Cannot create new tasks."}), 400

			try:
				# Parse params if it's a JSON string
				params = data.get("params", {})
				if isinstance(params, str):
					try:
						params = json.loads(params) if params.strip() else {}
					except json.JSONDecodeError:
						return jsonify({"error": "Invalid JSON in params field"}), 400

				# Parse timeout if provided
				timeout = data.get("timeout")
				if timeout is not None:
					timeout = int(timeout) if timeout else None

				# Parse priority
				priority = int(data.get("priority", 0))

				task_id = tasks_service.submit(
					task_name=data["task_name"],
					params=params,
					priority=priority,
					timeout=timeout
				)
				# Emit Socket.IO event to refresh tasks page
				socketio.broadcast_to_page('tasks', 'refresh_page', {})

				return jsonify({"task_id": task_id, "message": "Task created successfully"})
			except KeyError as e:
				return jsonify({"error": str(e)}), 404
			except Exception as e:
				return jsonify({"error": str(e)}), 500

		# Build DSL for GET request
		try:
			running = tasks_service.get_running_tasks()

			all_tasks = []
			for status in [Task.TaskStatus.PENDING, Task.TaskStatus.RUNNING,
						   Task.TaskStatus.COMPLETED, Task.TaskStatus.FAILED,
						   Task.TaskStatus.TIMEOUT]:
				all_tasks.extend(tasks_service.task_model.get_by_status(status))

			all_tasks.sort(key=lambda x: x.get('created_at', 0), reverse=True)
			all_tasks = all_tasks[:100]

			# Convert task status to strings and timestamps to milliseconds
			for task in all_tasks:
				task['status'] = str(task['status'])
				# Convert Unix timestamps from seconds to milliseconds for JavaScript
				if task.get('created_at'):
					task['created_at'] = int(task['created_at'] * 1000)
				if task.get('started_at'):
					task['started_at'] = int(task['started_at'] * 1000)
				if task.get('completed_at'):
					task['completed_at'] = int(task['completed_at'] * 1000)

			registered_tasks = list(tasks_service._registry.keys())

			return jsonify(
				PageBuilder(
					title="Tasks System",
					description="Background task execution management"
				).add_section(
					SectionBuilder("System Status").add_info_grid([
						create_info_item("Workers Enabled", "Yes" if tasks_service.workers_enabled else "No"),
						create_info_item("Worker Count", tasks_service._worker_count),
						create_info_item("Paused", "Yes" if tasks_service.is_paused else "No", type="status"),
						create_info_item("Running Tasks", len(running))
					], columns=4)
				)
				.add_section(
					SectionBuilder("Tasks").add_table(
						TableBuilder(all_tasks)
						.add_column("id", "ID", type="number", width="80px")
						.add_column("name", "Task Name", type="code")
						.add_status_column(
							"status",
							"Status",
							config={
								"PENDING": {"label": "Pending", "variant": "info"},
								"RUNNING": {"label": "Running", "variant": "warning"},
								"COMPLETED": {"label": "Completed", "variant": "success"},
								"FAILED": {"label": "Failed", "variant": "error"},
								"TIMEOUT": {"label": "Timeout", "variant": "error"}
							}
						)
						.add_column("created_at", "Created", type="date")
						.add_column("priority", "Priority", type="number", width="100px")
						.add_hidden_column("result")  # Hidden column for task result (available in modal)
						.add_header_action("pause", "Pause System", 
							ActionBuilder().api_call("/api/v1/tasks/system/pause", method="POST").on_success(
								message="System paused",
								action=ActionBuilder().refresh()
							)
						)
						.add_header_action("resume", "Resume System", 
							ActionBuilder().api_call("/api/v1/tasks/system/resume", method="POST").on_success(
								message="System resumed",
								action=ActionBuilder().refresh()
							)
						)
						.add_header_action("cleanup", "Cleanup Old Tasks", 
							ActionBuilder().api_call("/api/v1/tasks/cleanup", method="POST").on_success(
								message="Cleanup complete",
								action=ActionBuilder().refresh()
							)
						)
						.add_header_action("create", "Create Task", ActionBuilder().open_modal("create_task"))
						.add_row_action(
							"requeue",
							"Requeue",
							ActionBuilder().api_call(
								ValueRefBuilder.computed("/admin/tasks/{id}/requeue", id=ValueRefBuilder.field("row", "id")),
								method="POST"
							).on_success(
								message="Task requeued",
								action=ActionBuilder().refresh()
							),
							confirm_message="Requeue this task?"
						)
						.on_row_click(
							action="open-modal",
							target="task_detail",
							params={
								"id": ValueRefBuilder.field("row", "id"),
								"name": ValueRefBuilder.field("row", "name"),
								"status": ValueRefBuilder.field("row", "status"),
								"created_at": ValueRefBuilder.field("row", "created_at"),
								"priority": ValueRefBuilder.field("row", "priority"),
								"params": ValueRefBuilder.field("row", "params"),
								"result": ValueRefBuilder.field("row", "result"),
								"error": ValueRefBuilder.field("row", "error")
							}
						)
					)
				)
				.add_modal("create_task", ModalDefinition(
					title="Create New Task",
					size="medium",
					content=[
						FormBuilder(
							submit_action=ActionBuilder().api_call("/admin/tasks", method="POST", body={
								"task_name": ValueRefBuilder.field("form", "task_name"),
								"params": ValueRefBuilder.field("form", "params"),
								"priority": ValueRefBuilder.field("form", "priority"),
								"timeout": ValueRefBuilder.field("form", "timeout")
							}).on_success(
								message="Task created successfully",
								action=ActionBuilder().close_modal("create_task").on_success(action=ActionBuilder().refresh())
							)
						)
						.add_select_field("task_name", "Task Name", [FormFieldOption(value=task, label=task, description="") for task in registered_tasks], required=True)
						.add_field("params", "Parameters (JSON)", type="textarea", placeholder='{"key": "value"}', helpText="JSON object with task parameters")
						.add_field("priority", "Priority", type="number", defaultValue=0)
						.add_field("timeout", "Timeout (seconds)", type="number", placeholder="Optional")
						.set_cancel_action(ActionBuilder().close_modal("create_task"))
					.build()],
					closeOnOverlayClick=True
				))
				.add_modal("task_detail", ModalDefinition(
					title="Task Details",
					size="large",
					content=[
						InfoGridComponent(
							type="info-grid",
							items=[
								create_info_item("Task ID", ValueRefBuilder.field("data", "id")),
								create_info_item("Task Name", ValueRefBuilder.field("data", "name"), type="code"),
								create_info_item("Status", ValueRefBuilder.field("data", "status"), type="status"),
								create_info_item("Priority", ValueRefBuilder.field("data", "priority")),
								create_info_item("Created At", ValueRefBuilder.field("data", "created_at"), type="date")
							],
							columns=2
						),
						DividerComponent(type="divider", label="Parameters"),
						CodeBlockComponent(
							type="code-block",
							content=ValueRefBuilder.field("data", "params"),
							language="json",
							copyable=True
						),
						DividerComponent(type="divider", label="Result"),
						CodeBlockComponent(
							type="code-block",
							content=ValueRefBuilder.coalesce(
								ValueRefBuilder.field("data", "result"),
								ValueRefBuilder.literal("No result yet")
							),
							language="json",
							copyable=True
						)
					],
					closeOnOverlayClick=True
				))
				.set_realtime(
					socket_events=[
						SocketEventHandler(
							event="refresh_page",
							handler="refresh-page"
						),
						SocketEventHandler(
							event="task_update",
							handler="refresh-page"
						)
					]
				).build()
			)

		except Exception as e:
			traceback.print_exc()
			return jsonify({"title": "Tasks System", "error": f"Failed to get tasks: {str(e)}"})

	@register("/tasks/<int:task_id>/requeue", methods=["POST"])
	@describe("Requeue a pending task", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def requeue_task(self, task_id: int):
		"""Requeue a pending task that's not in the queue (e.g., after restart)"""
		socketio = self.manager.get[NullSocketIO]("services.socketio")
		tasks_service = self.manager.get[Tasks]("services.tasks")
		try:
			if tasks_service.is_paused:
				return jsonify({"error": "Task system is paused. Cannot requeue tasks."}), 400

			success = tasks_service.requeue(task_id)
			if success:
				socketio.broadcast_to_page('tasks', 'refresh_page', {})
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
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def manage_settings(self):
		settings_service = self.manager.get[Settings]("services.settings")

		page = (PageBuilder(title="Settings", description="See, manage and edit global service settings")
			.add_section(
				SectionBuilder("Settings")
				.add_table(
					TableBuilder([
						{"name": k, "value": getattr(settings_service, k)} |v
							for k, v in settings_service.get_settings_schema().items()
					])
					.add_column("name", "setting", type="text", width="100px", sortable=True)
					.add_column("value", "value example", type="text", width="100px", sortable=True)
					.add_column("default", "default", type="text", width="100px")
					.add_column("description", "description", type="text", width="auto", truncate=True)
					.on_row_click("open-modal", "config-settings", params={
						"name": ValueRefBuilder.field("row", "name"),
						"value": ValueRefBuilder.field("row", "value"),
						"default": ValueRefBuilder.field("row", "default"),
						"description": ValueRefBuilder.field("row", "description"),
					})
				)
			)
			.add_modal(
				"config-settings",
				ModalDefinition(title="Edit settings", size="fullscreen", closeOnOverlayClick=True,
					content=[
						FormBuilder(
							submit_action=ActionBuilder().api_call("/admin/settings", method="POST", body={
								"name": ValueRefBuilder.field("form", "name"),
								"value": ValueRefBuilder.field("form", "value"),
							}).on_success(
								action=ActionBuilder().show_toast(
									message=ValueRefBuilder.coalesce(
										ValueRefBuilder.field("form", "value"),
										ValueRefBuilder.field("data", "default")
									)
								)
								.close_modal("config-settings")
							)	
						)
						.add_field("value", "New value", type="text",
							 placeholder=ValueRefBuilder.field("data", "default"),
							 defaultValue=ValueRefBuilder.field("data", "value")
						)
						.build()
					]
				)
			)
		)
		return jsonify(page.build())



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
	@describe("Get database info page", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_database(self):
		"""Database admin page with tabs for Tables and Query Stats."""
		settings = self.manager.get[Settings]("services.settings")
		db_path = settings.db

		file_size = 0
		if os.path.exists(db_path):
			file_size = os.path.getsize(db_path)

		# Count tables and rows for stats
		total_tables = len(list(self.models.all()))
		total_rows = sum(model.get_count() for model in self.models.all())

		page = PageBuilder(title="Database", description="Database management and information")

		# Stats section
		page.add_section(SectionBuilder("Overview")
			.add_stats_cards([
				create_stat_card("Total Tables", total_tables),
				create_stat_card("Total Rows", total_rows),
				create_stat_card("File Size", f"{file_size / 1024:.2f} KB"),
			], columns=3)
			.add_info_grid([
				create_info_item("Path", db_path, type="code", copyable=True),
				create_info_item("Type", "SQLite3"),
			], columns=2))

		# Tabs for Tables and Query Stats
		tables_tab = (TabBuilder("tables", "Tables")
			.add_component(create_defer(
				id="tables-defer",
				endpoint="/admin/database/tables",
				trigger=create_defer_trigger_immediate(),
				loading_state=create_skeleton(variant="table", rows=5)
			))
		)

		queries_tab = (TabBuilder("queries", "Query Stats")
			.add_component(create_defer(
				id="queries-defer",
				endpoint="/admin/database/queries",
				trigger=create_defer_trigger_immediate(),
				loading_state=create_skeleton(variant="table", rows=5)
			))
		)

		tabs = (TabsBuilder()
			.add_tab(tables_tab)
			.add_tab(queries_tab)
			.default_tab("tables")
			.variant("underlined")
			.build()
		)
		page.add_section(SectionBuilder().add_component(tabs))

		# Modal for viewing table data
		page.add_modal("view-table-data",
			ModalBuilder(
				title=ValueRefBuilder.computed("Table: {table}", table=ValueRefBuilder.field("data", "table")),
				size="fullscreen"
			)
			.close_on_overlay_click(True)
			.add_component(create_defer(
				endpoint=ValueRefBuilder.computed("/admin/database/table/{table}/view", table=ValueRefBuilder.field("data", "table")),
				trigger=create_defer_trigger_immediate(),
				loading_state=create_skeleton(variant="table", rows=5),
				id="table-view-content"
			))
			.on_close(ActionBuilder().trigger_dynamic("tables-defer"))
		)

		# Modal for adding a record
		page.add_modal("add-record",
			ModalBuilder(
				title=ValueRefBuilder.computed("Add Record to {table}", table=ValueRefBuilder.field("data", "table")),
				size="medium"
			)
			.close_on_overlay_click(True)
			.add_component(create_defer(
				endpoint=ValueRefBuilder.computed("/admin/database/table/{table}/form", table=ValueRefBuilder.field("data", "table")),
				trigger=create_defer_trigger_immediate(),
				loading_state=create_skeleton(variant="text", lines=5)
			))
		)

		# Modal for EXPLAIN query
		page.add_modal("explain-result",
			ModalBuilder(title="EXPLAIN Query", size="large")
			.close_on_overlay_click(True)
			.add_component(create_defer(
				endpoint="/admin/database/explain",
				method="POST",
				trigger=create_defer_trigger_immediate(),
				body={
					"query": ValueRefBuilder.field("data", "query"),
					"params": ValueRefBuilder.field("data", "params")
				},
				loading_state=create_skeleton(variant="table", rows=3)
			))
		)

		return jsonify(page.build())

	@register("/database/tables", methods=["GET"])
	@describe("Get tables list component", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_database_tables(self):
		"""Returns DSL components for the tables list."""
		tables_info = []
		for model in self.models.all():
			count = model.get_count()
			column_defs = model.get_column_definitions()
			tables_info.append({
				"name": model.name,
				"rows": count,
				"columns": len(column_defs),
			})

		table = TableBuilder(tables_info)
		table.add_column("name", "Table Name", type="text", sortable=True)
		table.add_column("rows", "Row Count", type="number", sortable=True)
		table.add_column("columns", "Columns", type="number", sortable=True)
		table.set_sortable(True)
		table.add_row_action(
			id="view-data",
			label="View",
			action=ActionBuilder().open_modal("view-table-data", modal_data={
				"table": ValueRefBuilder.field("row", "name")
			})
		)

		return jsonify([table.build()])

	@register("/database/queries", methods=["GET"])
	@describe("Get query stats component", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_database_queries(self):
		"""Returns DSL components for query statistics."""
		services_manager = self.manager.get[Manager[ABCService]]("services")
		db_service = services_manager.get[DB]("db")

		db_metrics = db_service.get_metrics()
		query_patterns = db_metrics.get('query_patterns', [])

		if not query_patterns:
			return jsonify([
				EmptyStateComponent(type="empty-state", message="No query statistics available", description="Execute some queries to see statistics here.")
			])

		# Format for table
		queries_data = []
		for pattern in query_patterns[:50]:  # Limit to top 50
			query = pattern.get('example_query', '')
			queries_data.append({
				"query": query[:100] + "..." if len(query) > 100 else query,
				"full_query": query,
				"params": pattern.get('example_params', '()'),
				"count": pattern.get('count', 0),
				"avg_time": f"{pattern.get('avg_time', 0) * 1000:.2f}ms",
				"total_time": f"{pattern.get('total_time', 0) * 1000:.2f}ms",
				"errors": pattern.get('error_count', 0)
			})

		table = TableBuilder(queries_data)
		table.table["density"] = "compact"
		table.add_column("query", "Query", type="code", sortable=True, truncate=True)
		table.add_column("count", "Executions", type="number", sortable=True, width="100px")
		table.add_column("avg_time", "Avg Time", type="text", sortable=True, width="100px")
		table.add_column("total_time", "Total Time", type="text", sortable=True, width="100px")
		table.add_column("errors", "Errors", type="number", sortable=True, width="80px")
		table.add_row_action(
			id="explain-query",
			label="EXPLAIN",
			action=ActionBuilder().open_modal("explain-result", modal_data={
				"query": ValueRefBuilder.field("row", "full_query"),
				"params": ValueRefBuilder.field("row", "params")
			})
		)

		return jsonify([table.build()])

	@register("/database/table/<table_name>/view", methods=["GET"])
	@describe("Get table view component with data", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_table_view(self, table_name: str):
		"""Returns DSL components for viewing table data."""
		page = int(request.args.get('page', 1))
		page_size = int(request.args.get('pageSize', 10))
		offset = (page - 1) * page_size

		# Find the model
		model = None
		for m in self.models.all():
			if m.name == table_name:
				model = m
				break

		if not model:
			return jsonify([
				AlertComponent(type="alert", title="Error", message=f"Table '{table_name}' not found", variant="error")
			]), 404

		table_data = model.get_all(limit=page_size, offset=offset)
		total_count = model.get_count()
		columns = model.get_column_definitions()
		total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

		components = [
			InfoGridComponent(type="info-grid", columns=3, items=[
				InfoGridItem(label="Table", value=table_name, type="code"),
				InfoGridItem(label="Total Rows", value=str(total_count), type="text"),
				InfoGridItem(label="Page", value=f"{page} / {total_pages}", type="text"),
			]),
			DividerComponent(type="divider"),
		]

		# Build table with actions
		table = TableBuilder(table_data)
		for col in columns:
			table.add_column(col['key'], col.get('label', col['key']), type=col.get('type', 'text'), sortable=col.get('sortable', False), truncate=col.get('truncate', False))
		table.table["density"] = "compact"
		table.set_sortable(True)

		# Header action to add record
		table.add_header_action(
			id="add-record",
			label="Add Record",
			action=ActionBuilder().open_modal("add-record", modal_data={"table": table_name})
		)

		# Row action to delete
		table.add_row_action(
			id="delete-record",
			label="Delete",
			confirm_message=ValueRefBuilder.computed("Delete record {id}?", id=ValueRefBuilder.field("row", "id")),
			action=ActionBuilder()
				.api_call(
					endpoint=ValueRefBuilder.computed(f"/admin/database/table/{table_name}/delete/{{id}}", id=ValueRefBuilder.field("row", "id")),
					method="DELETE"
				)
				.on_success(
					message="Record deleted",
					action=ActionBuilder().trigger_dynamic("table-view-content")
				)
				.on_error(message="Failed to delete record")
		)

		# Server-side pagination
		table.set_pagination(
			enabled=True,
			page_size=page_size,
			mode="server",
			total_items=total_count,
			current_page=page,
			on_page_change=ActionBuilder().trigger_dynamic("table-view-content", params={
				"page": ValueRefBuilder.field("pagination", "pageNumber"),
				"pageSize": ValueRefBuilder.field("pagination", "pageSize")
			})
		)

		components.append(table.build())
		return jsonify(components)

	@register("/database/table/<table_name>/form", methods=["GET"])
	@describe("Get add record form component", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_table_form(self, table_name: str):
		"""Returns DSL form component for adding a record."""
		# Find the model
		model = None
		for m in self.models.all():
			if m.name == table_name:
				model = m
				break

		if not model:
			return jsonify([
				AlertComponent(type="alert", title="Error", message=f"Table '{table_name}' not found", variant="error")
			]), 404

		# Get column definitions and build form fields
		columns = model.get_column_definitions()
		fields = []
		for col in columns:
			if col['key'] == 'id':
				continue  # Skip auto-increment ID
			field_type = "text"
			if col.get('type') == 'number':
				field_type = "number"
			elif col.get('type') == 'boolean':
				field_type = "checkbox"
			fields.append({
				"name": col['key'],
				"label": col.get('label', col['key']),
				"type": field_type,
				"required": col.get('required', False)
			})

		form = FormComponent(
			type="form",
			fields=fields,
			layout="vertical",
			submitAction=ActionBuilder()
				.api_call(
					endpoint=f"/admin/database/table/{table_name}/create",
					method="POST",
					body=ValueRefBuilder.field("form", "self")
				)
				.on_success(
					message="Record created successfully",
					action=ActionBuilder().close_modal("add-record").on_success(
						action=ActionBuilder().trigger_dynamic("table-view-content").on_success(
							action=ActionBuilder().trigger_dynamic("tables-defer")  # Also refresh tables list row count
						)
					)
				)
				.on_error(message="Failed to create record")
				.build(),
			cancelAction=ActionBuilder().close_modal("add-record").build()
		)

		return jsonify([form])

	@register("/database/table/<table_name>", methods=["GET"])
	@describe("Get table data with pagination", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_table_data(self, table_name: str):
		# Get pagination params (1-indexed pages from frontend)
		page = int(request.args.get('page', 1))
		page_size = int(request.args.get('pageSize', 10))

		# Convert to 0-indexed offset for database
		offset = (page - 1) * page_size

		# Find the model by name
		model = None
		for m in self.models.all():
			if m.name == table_name:
				model = m
				break

		if not model:
			return jsonify({"error": f"Model '{table_name}' not found"}), 404

		# Get data using model methods
		table_data = model.get_all(limit=page_size, offset=offset)
		total_count = model.get_count()
		columns = model.get_column_definitions()
		total_pages = (total_count + page_size - 1) // page_size

		return jsonify({
			"tableData": table_data,
			"columns": columns,
			"totalRecords": total_count,
			"currentPage": page,
			"totalPages": total_pages,
			"pageSize": page_size
		})

	@register("/database/table/<table_name>/delete/<int:record_id>", methods=["DELETE"])
	@describe("Delete a record from a table", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def delete_table_record(self, table_name: str, record_id: int):
		# Find the model by name
		model = None
		for m in self.models.all():
			if m.name == table_name:
				model = m
				break

		if not model:
			return jsonify({"error": f"Model '{table_name}' not found"}), 404

		# Delete the record
		try:
			success = model.delete(record_id)
			if success:
				return jsonify({"success": True, "message": f"Record {record_id} deleted successfully"})
			else:
				return jsonify({"error": f"Record {record_id} not found"}), 404
		except Exception as e:
			return jsonify({"error": str(e)}), 500

	@register("/database/table/<table_name>/create", methods=["POST"])
	@describe("Create a new record in a table", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def create_table_record(self, table_name: str):
		# Find the model by name
		model = None
		for m in self.models.all():
			if m.name == table_name:
				model = m
				break

		if not model:
			return jsonify({"error": f"Model '{table_name}' not found"}), 404

		# Get data from request
		data = request.get_json()

		# Call create method with data
		try:
			# Get the create method signature to validate params
			import inspect
			import enum
			from typing import get_origin, get_args

			sig = inspect.signature(model.create)
			params = {}

			for param_name, param in sig.parameters.items():
				if param_name == 'self':
					continue

				# Get value from request data
				if param_name in data:
					value = data[param_name]
					annotation = param.annotation

					# Convert to correct type if needed
					if annotation != inspect.Parameter.empty:
						# Handle Optional types
						origin = get_origin(annotation)
						if origin is not None:
							args = get_args(annotation)
							# Check if it's Optional (Union with None)
							if len(args) == 2 and type(None) in args:
								annotation = args[0] if args[1] is type(None) else args[1]

						try:
							# Check for Enum types
							if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
								# Convert value to enum member
								value = annotation(value)
							elif annotation == int:
								value = int(value)
							elif annotation == float:
								value = float(value)
							elif annotation == bool:
								value = bool(value)
						except (TypeError, ValueError) as e:
							# If conversion fails, pass the value as-is and let the model handle it
							pass

					params[param_name] = value
				elif param.default == inspect.Parameter.empty:
					# Required parameter missing
					return jsonify({"error": f"Missing required parameter: {param_name}"}), 400

			# Create the record
			record_id = model.create(**params)
			return jsonify({"success": True, "id": record_id, "message": "Record created successfully"})
		except Exception as e:
			return jsonify({"error": str(e)}), 500

	@register("/database/table/<table_name>/schema", methods=["GET"])
	@describe("Get the create method schema for a table", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_table_schema(self, table_name: str):
		# Find the model by name
		model = None
		for m in self.models.all():
			if m.name == table_name:
				model = m
				break

		if not model:
			return jsonify({"error": f"Model '{table_name}' not found"}), 404

		# Extract type hints from create method
		import inspect
		import enum
		from typing import get_type_hints, get_origin, get_args

		sig = inspect.signature(model.create)
		fields = []

		for param_name, param in sig.parameters.items():
			if param_name == 'self':
				continue

			# Determine field type
			field_type = "text"
			field_options = None
			annotation = param.annotation

			if annotation != inspect.Parameter.empty:
				# Handle Optional types
				origin = get_origin(annotation)
				if origin is not None:
					args = get_args(annotation)
					# Check if it's Optional (Union with None)
					if len(args) == 2 and type(None) in args:
						annotation = args[0] if args[1] is type(None) else args[1]

				# Check if annotation is a class (to avoid errors with type checking)
				try:
					# Check for Enum types
					if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
						field_type = "select"
						# Build options from enum values
						field_options = [
							{
								"value": member.value,
								"label": member.name.replace("_", " ").title()
							}
							for member in annotation
						]
					# Map Python types to form field types
					elif issubclass(annotation, int):
						field_type = "number"
					elif issubclass(annotation, float):
						field_type = "number"
					elif issubclass(annotation, bool):
						field_type = "checkbox"
					elif issubclass(annotation, str):
						field_type = "text"
					else:
						print("type", param_name, param, annotation)
				except TypeError:
					# annotation is not a class (might be a generic type)
					print("type", param_name, param, annotation)

			# Build field definition
			field = {
				"name": param_name,
				"label": param_name.replace("_", " ").title(),
				"type": field_type,
				"required": param.default == inspect.Parameter.empty
			}

			if field_options is not None:
				field["options"] = field_options

			if param.default != inspect.Parameter.empty:
				field["defaultValue"] = param.default

			fields.append(field)

		return jsonify({"fields": fields})

	@register("/database/explain", methods=["POST"])
	@describe("Run EXPLAIN on a SQL query", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def explain_query(self):
		try:
			data = request.get_json()
			query = data.get('query', '')
			params_str = data.get('params', '()')

			if not query:
				return jsonify({"error": "Query is required"}), 400
			try:
				# Handle empty or whitespace-only strings
				if not params_str or params_str.strip() in ('', '()'):
					params = ()
				else:
					# Log what we're trying to parse
					self.logs.debug(f"Parsing parameters", service="admin", params_str=params_str)
					params = ast.literal_eval(params_str)
					# Ensure params is a tuple
					if not isinstance(params, tuple):
						if isinstance(params, list):
							params = tuple(params)
						else:
							params = (params,)
					self.logs.debug(f"Parsed parameters", service="admin", params=params, params_type=type(params).__name__)
			except Exception as parse_error:
				# If parsing fails, log the error and use empty tuple
				self.logs.error(f"Failed to parse parameters", service="admin",
				               params_str=params_str, error=str(parse_error))
				params = ()

			# Get database service
			services_manager = self.manager.get[Manager[ABCService]]("services")
			db_service = services_manager.get[DB]("db")

			# Run EXPLAIN QUERY PLAN
			with db_service() as cursor:
				# Use the raw cursor for EXPLAIN
				explain_query = f"EXPLAIN QUERY PLAN {query}"

				# Log what we're about to execute
				self.logs.debug(f"Executing EXPLAIN", service="admin",
				               query=query[:100], params=params, has_params=bool(params))

				# Execute EXPLAIN with parameters if provided
				try:
					if params:
						# EXPLAIN needs the same parameters as the original query
						cursor._cursor.execute(explain_query, params)
					else:
						cursor._cursor.execute(explain_query)
					results = cursor._cursor.fetchall()

					self.logs.debug(f"EXPLAIN successful", service="admin",
					               result_count=len(results))
				except Exception as e:
					# If EXPLAIN fails, provide detailed error
					self.logs.error(f"EXPLAIN failed", service="admin",
					               query=query, params=params, error=str(e))
					traceback.print_exception(e)
					return jsonify([
						AlertComponent(type="alert", title="EXPLAIN Failed", message=f"{str(e)}", variant="error"),
						InfoGridComponent(type="info-grid", columns=1, items=[
							InfoGridItem(label="Query", value=query, type="code"),
							InfoGridItem(label="Params", value=str(params), type="code"),
						])
					]), 400

				# Format results as table data
				explanation = []
				for row in results:
					# SQLite EXPLAIN QUERY PLAN returns: id, parent, notused, detail
					if len(row) >= 4:
						explanation.append({
							"column": "Plan",
							"value": f"[{row[0]}] {row[3]}"
						})
					else:
						explanation.append({
							"column": "Detail",
							"value": str(row)
						})

				# Add query info
				explanation.insert(0, {
					"column": "Query Type",
					"value": query.strip().split()[0].upper()
				})

				if params:
					explanation.insert(1, {
						"column": "Parameters",
						"value": str(params)
					})

			# Return DSL components for Defer
			components = [
				InfoGridComponent(type="info-grid", columns=1, items=[
					InfoGridItem(label="Query", value=query, type="code"),
				]),
				DividerComponent(type="divider"),
				TableComponent(
					type="table",
					data=explanation,
					columns=[
						ColumnDefinition(key="column", label="Type", type="text", sortable=False, width="150px"),
						ColumnDefinition(key="value", label="Detail", type="text", sortable=False, width="auto")
					],
					sortable=False,
					density="compact"
				)
			]
			return jsonify(components)

		except Exception as e:
			traceback.print_exc()
			return jsonify([
				AlertComponent(type="alert", title="Error", message=f"Failed to explain query: {str(e)}", variant="error")
			]), 500

	@register("/metrics/save", methods=["POST"])
	@describe("Save all metrics to disk", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def save_metrics(self):
		try:
			services_manager = self.manager.get[Manager[ABCService]]("services")
			db_service = services_manager.get[DB]("db")

			# Trigger immediate save of all metrics
			db_service.save_all_metrics()

			return jsonify({
				"success": True,
				"message": "All metrics saved to disk successfully"
			})

		except Exception as e:
			traceback.print_exc()
			return jsonify({"error": f"Failed to save metrics: {str(e)}"}), 500

	@register("/cache", methods=["GET"])
	@describe("Get cache info", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_cache(self):
		try:
			cache = self.manager.get[Cache]("services.cache")

			# Build DSL using builder utilities
			page = PageBuilder(
				title="Cache",
				description="Redis cache management"
			)

			# Add cache status info grid
			section = SectionBuilder("Status")
			section.add_info_grid([
				create_info_item("Ready", "Yes" if cache.ready else "No", type="status"),
				create_info_item("Type", type(cache).__name__, type="code")
			], columns=2)

			page.add_section(section)

			return jsonify(page.build())
		except Exception as e:
			# Fallback to error DSL
			page = PageBuilder(
				title="Cache",
				description=f"Failed to get cache info: {str(e)}"
			)
			return jsonify(page.build())

	@register("/logs", methods=["GET"])
	@describe("Get logs", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_logs(self):
		services_manager = self.manager.get[Manager[ABCService]]("services")

		# Get query parameters
		limit = int(request.args.get('limit', 100))
		level = request.args.get('level', None)

		# Get logs from the logging service
		try:
			logs_service = services_manager.get[Logs]("logs")
			logs = logs_service.get_recent_logs(limit=limit, level=level)
		except Exception as e:
			# Fallback if logs service is not available
			logs = [{
				"timestamp": datetime.now().isoformat(),
				"level": "ERROR",
				"logger": "admin",
				"message": f"Failed to retrieve logs: {str(e)}"
			}]

		# Sanitize log messages (remove ANSI codes and non-printable characters)
		for log in logs:
			if 'message' in log:
				log['message'] = SanitizeLogs(log['message'])

		# Build DSL
		page = PageBuilder(
			title="Logs",
			description=f"Application logs - Showing {len(logs)} most recent entries"
		)

		# Stats section with ID for real-time updates
		stats_section = SectionBuilder()
		stats_section.set_id("logs-stats")
		log_counts = {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0}
		for log in logs:
			log_level = log.get('level', 'INFO')
			log_counts[log_level] = log_counts.get(log_level, 0) + 1

		stats_section.add_stats_cards([
			create_stat_card("Total Logs", len(logs)),
			create_stat_card("Errors", log_counts['ERROR'] + log_counts['CRITICAL']),
			create_stat_card("Warnings", log_counts['WARNING']),
			create_stat_card("Info", log_counts['INFO'])
		], columns=4)

		page.add_section(stats_section)

		# Logs table section
		section = SectionBuilder("Recent Logs")

		# Build the logs table with compact density
		table = TableBuilder(logs)
		table.table["density"] = "compact"

		# Timestamp column - compact width, truncated, left-aligned
		timestamp_col: ColumnDefinition = ColumnDefinition(
			key="timestamp",
			label="Timestamp",
			type="date",
			sortable=True,
			width="180px",
			truncate=True,
			align="left"
		)
		table.table["columns"].append(timestamp_col)  # type: ignore

		# Level column with status badges - compact width, left-aligned
		level_col: ColumnDefinition = ColumnDefinition(
			key="level",
			label="Level",
			type="status",
			sortable=True,
			width="90px",
			align="left",
			renderer=ColumnRenderer(
				type="status-badge",
				config={
					"INFO": StatusBadgeConfig(label="Info", variant="success"),
					"WARNING": StatusBadgeConfig(label="Warning", variant="warning"),
					"ERROR": StatusBadgeConfig(label="Error", variant="error"),
					"DEBUG": StatusBadgeConfig(label="Debug", variant="info")
				}
			)
		)
		table.table["columns"].append(level_col)  # type: ignore

		# Logger column - compact width, truncated, left-aligned
		logger_col: ColumnDefinition = ColumnDefinition(
			key="logger",
			label="Logger",
			type="text",
			sortable=True,
			width="120px",
			truncate=True,
			align="left"
		)
		table.table["columns"].append(logger_col)  # type: ignore

		# Message column - takes remaining space, truncated, left-aligned
		message_col: ColumnDefinition = ColumnDefinition(
			key="message",
			label="Message",
			type="text",
			width="auto",
			truncate=True,
			align="left"
		)
		table.table["columns"].append(message_col)  # type: ignore

		# Header actions
		clear_logs_action = ActionBuilder()
		clear_logs_action.api_call("/admin/logs/clear", method="POST").on_success(
			message="Logs cleared successfully",
			action=ActionBuilder().refresh()
		)
		table.add_header_action("clear", "Clear Logs", clear_logs_action,
		                       confirm_message="Clear all logs? This cannot be undone.")

		refresh_action = ActionBuilder().refresh()
		table.add_header_action("refresh", "Refresh", refresh_action)

		# Add row click handler to open modal with full log details
		table.table["onRowClick"] = TableOnRowClick(
			action="open-modal",
			target="log_details",
			params={
				"timestamp": ValueRefBuilder.field("row", "timestamp"),
				"level": ValueRefBuilder.field("row", "level"),
				"logger": ValueRefBuilder.field("row", "logger"),
				"message": ValueRefBuilder.field("row", "message")
			}
		)

		section.add_table(table)
		page.add_section(section)

		# Log details modal
		log_details_modal = ModalDefinition(
			title="Log Details",
			size="medium",
			closeOnOverlayClick=True
		)

		# Info grid for log metadata
		log_info_grid = InfoGridComponent(
			type="info-grid",
			items=[
				InfoGridItem(
					label="Timestamp",
					value=ValueRefBuilder.field("data", "timestamp"),
					type="date"
				),
				InfoGridItem(
					label="Level",
					value=ValueRefBuilder.field("data", "level"),
					type="text"
				),
				InfoGridItem(
					label="Logger",
					value=ValueRefBuilder.field("data", "logger"),
					type="text"
				)
			],
			columns=3
		)

		# Code block for full message (no language specified for plain text)
		log_message_block = CodeBlockComponent(
			type="code-block",
			content=ValueRefBuilder.field("data", "message"),
			copyable=True
		)

		log_details_modal["content"] = [log_info_grid, log_message_block]

		page.add_modal("log_details", log_details_modal)

		# Add real-time updates via Socket.IO and polling for stats
		page.set_realtime(
			socket_events=[
				SocketEventHandler(
					event="refresh_page",
					handler="refresh-page"
				)
			],
			polling=PollingConfig(
				interval=2000,  # Poll every 2 seconds
				endpoint="/admin/logs/stats",
				componentId="logs-stats"
			)
		)

		return jsonify(page.build())

	@register("/logs/clear", methods=["POST"])
	@describe("Clear all logs", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def clear_logs(self):
		services_manager = self.manager.get[Manager[ABCService]]("services")

		try:
			logs_service = services_manager.get[Logs]("logs")
			logs_service.clear_logs()
			return jsonify({"message": "Logs cleared successfully"})
		except Exception as e:
			return jsonify({"error": f"Failed to clear logs: {str(e)}"}), 500

	@register("/logs/stats", methods=["GET"])
	@describe("Get logs statistics for real-time updates", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_logs_stats(self):
		services_manager = self.manager.get[Manager[ABCService]]("services")

		# Get query parameters (use same defaults as main logs endpoint)
		limit = int(request.args.get('limit', 100))
		level = request.args.get('level', None)

		# Get logs from the logging service
		try:
			logs_service = services_manager.get[Logs]("logs")
			logs = logs_service.get_recent_logs(limit=limit, level=level)
		except Exception as e:
			# Fallback if logs service is not available
			logs = [{
				"timestamp": datetime.now().isoformat(),
				"level": "ERROR",
				"logger": "admin",
				"message": f"Failed to retrieve logs: {str(e)}"
			}]

		# Calculate stats
		log_counts = {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0}
		for log in logs:
			log_level = log.get('level', 'INFO')
			log_counts[log_level] = log_counts.get(log_level, 0) + 1

		# Build stats section
		stats_section = SectionBuilder()
		stats_section.set_id("logs-stats")
		stats_section.add_stats_cards([
			create_stat_card("Total Logs", len(logs)),
			create_stat_card("Errors", log_counts['ERROR'] + log_counts['CRITICAL']),
			create_stat_card("Warnings", log_counts['WARNING']),
			create_stat_card("Info", log_counts['INFO'])
		], columns=4)

		return jsonify(stats_section.build())

	@register("/metrics", methods=["GET"])
	@describe("Get metrics", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_metrics(self):
		services_manager = self.manager.get[Manager[ABCService]]("services")

		try:
			metrics_service = services_manager.get[NullMetrics]("metrics")

			if not metrics_service.ready:
				page = PageBuilder(
					title="Metrics",
					description="Application metrics and monitoring"
				)
				error_section = SectionBuilder()
				error_section.add_alert(
					"Metrics service not available. Enable metrics in settings.",
					variant="warning"
				)
				page.add_section(error_section)
				return jsonify(page.build())

			stats = metrics_service.get_stats()

			# Build DSL page
			page = PageBuilder(
				title="Metrics",
				description="Real-time application performance metrics"
			)

			# Overview stats section
			stats_section = SectionBuilder()
			stats_section.set_id("metrics-stats")

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

			error_rate_pct = stats['overview']['error_rate'] * 100

			stats_section.add_stats_cards([
				create_stat_card("Total Requests", stats['overview']['total_requests'], icon="📊"),
				create_stat_card("Active Requests", stats['overview']['active_requests'], icon="⚡"),
				create_stat_card("Total Errors", stats['overview']['total_errors'], icon="❌"),
				create_stat_card("Error Rate", f"{error_rate_pct:.2f}%", icon="📈"),
				create_stat_card("Uptime", uptime_formatted, icon="⏱️")
			], columns=5)

			# Add save button
			stats_section.add_button(
				id="save-metrics",
				label="Save Metrics to Disk",
				action=ActionBuilder()
					.api_call(endpoint="/admin/metrics/save", method="POST")
					.on_success(message="All metrics saved successfully")
					.on_error(message="Failed to save metrics"),
				variant="secondary"
			)

			page.add_section(stats_section)

			# Endpoints table section
			endpoints_section = SectionBuilder("Endpoint Performance")

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
				})

			endpoints_list.sort(key=lambda x: x['request_count'], reverse=True)

			# Build table
			table = TableBuilder(endpoints_list)
			table.table["density"] = "compact"

			# Endpoint column
			endpoint_col: ColumnDefinition = ColumnDefinition(
				key="endpoint",
				label="Endpoint",
				type="text",
				sortable=True,
				width="auto",
				align="left"
			)
			table.table["columns"].append(endpoint_col)

			# Request count column
			requests_col: ColumnDefinition = ColumnDefinition(
				key="request_count",
				label="Requests",
				type="number",
				sortable=True,
				width="100px",
				align="right"
			)
			table.table["columns"].append(requests_col)

			# Error count column
			errors_col: ColumnDefinition = ColumnDefinition(
				key="error_count",
				label="Errors",
				type="number",
				sortable=True,
				width="80px",
				align="right"
			)
			table.table["columns"].append(errors_col)

			# Error rate column with status badge
			error_rate_col: ColumnDefinition = ColumnDefinition(
				key="error_rate",
				label="Error Rate",
				type="text",
				sortable=True,
				width="100px",
				align="right"
			)
			table.table["columns"].append(error_rate_col)

			# Average response time column
			avg_time_col: ColumnDefinition = ColumnDefinition(
				key="avg_response_time",
				label="Avg Time",
				type="text",
				sortable=True,
				width="100px",
				align="right"
			)
			table.table["columns"].append(avg_time_col)

			# P95 response time column
			p95_col: ColumnDefinition = ColumnDefinition(
				key="p95_response_time",
				label="P95",
				type="text",
				sortable=True,
				width="100px",
				align="right"
			)
			table.table["columns"].append(p95_col)

			# P99 response time column
			p99_col: ColumnDefinition = ColumnDefinition(
				key="p99_response_time",
				label="P99",
				type="text",
				sortable=True,
				width="100px",
				align="right"
			)
			table.table["columns"].append(p99_col)

			# Add refresh action
			refresh_action = ActionBuilder().refresh()
			table.add_header_action("refresh", "Refresh", refresh_action, icon="🔄")

			endpoints_section.add_table(table)
			page.add_section(endpoints_section)

			# Charts section
			charts_section = SectionBuilder("Performance Charts")

			# 1. Bar Chart - Top 5 Endpoints by Request Count (reduced from 10 for readability)
			top_endpoints = sorted(endpoints_list, key=lambda x: x['request_count'], reverse=True)[:5]
			bar_chart_data = []
			for ep in top_endpoints:
				# Truncate long endpoint names
				endpoint_name = ep['endpoint']
				if len(endpoint_name) > 30:
					endpoint_name = '...' + endpoint_name[-27:]
				bar_chart_data.append({
					'name': endpoint_name,
					'Requests': ep['request_count'],
					'Errors': ep['error_count']
				})

			if bar_chart_data:
				bar_chart = ChartBuilder("bar", bar_chart_data)
				bar_chart.add_series("Requests", "Requests", "#10b981")
				bar_chart.add_series("Errors", "Errors", "#ef4444")
				bar_chart.set_x_axis("name")
				bar_chart.set_y_axis("Count")
				bar_chart.set_legend(True)
				bar_chart.set_height(350)
				charts_section.add_chart(bar_chart)

			# 2. Line Chart - Response Time Comparison (Top 3 for clarity)
			top_3_endpoints = sorted(endpoints_list, key=lambda x: x['request_count'], reverse=True)[:3]

			if len(top_3_endpoints) > 0:
				# Create separate data points for each metric type
				line_chart_data = []
				for ep in top_3_endpoints:
					endpoint_name = ep['endpoint']
					if len(endpoint_name) > 20:
						endpoint_name = '...' + endpoint_name[-17:]

					avg_time = float(ep['avg_response_time'].replace('ms', ''))
					p95_time = float(ep['p95_response_time'].replace('ms', ''))
					p99_time = float(ep['p99_response_time'].replace('ms', ''))

					line_chart_data.append({
						'name': endpoint_name,
						'Avg': round(avg_time, 2),
						'P95': round(p95_time, 2),
						'P99': round(p99_time, 2)
					})

				line_chart = ChartBuilder("bar", line_chart_data)  # Using bar instead of line for better readability
				line_chart.add_series("Avg", "Average", "#3b82f6")
				line_chart.add_series("P95", "95th Percentile", "#f59e0b")
				line_chart.add_series("P99", "99th Percentile", "#ef4444")
				line_chart.set_x_axis("name")
				line_chart.set_y_axis("Time (ms)")
				line_chart.set_legend(True)
				line_chart.set_height(350)
				charts_section.add_chart(line_chart)

			# 3. Pie Chart - HTTP Status Code Distribution (simplified)
			status_code_totals: dict = {}
			for endpoint_data in stats['endpoints'].values():
				for status_code, count in endpoint_data['status_codes'].items():
					status_code_totals[status_code] = status_code_totals.get(status_code, 0) + count

			# Group status codes by category for better visualization
			status_categories = {
				'2xx Success': 0,
				'3xx Redirect': 0,
				'4xx Client Error': 0,
				'5xx Server Error': 0
			}

			for code, count in status_code_totals.items():
				code_int = int(code)
				if 200 <= code_int < 300:
					status_categories['2xx Success'] += count
				elif 300 <= code_int < 400:
					status_categories['3xx Redirect'] += count
				elif 400 <= code_int < 500:
					status_categories['4xx Client Error'] += count
				elif 500 <= code_int < 600:
					status_categories['5xx Server Error'] += count

			pie_chart_data = [
				{'name': category, 'value': count}
				for category, count in status_categories.items()
				if count > 0  # Only include categories with data
			]

			if len(pie_chart_data) > 0:
				pie_chart = ChartBuilder("pie", pie_chart_data)
				pie_chart.add_series("value", "Requests", "#8884d8")
				pie_chart.set_legend(True)
				pie_chart.set_height(350)
				charts_section.add_chart(pie_chart)

			page.add_section(charts_section)

			# Database metrics section
			db_section = SectionBuilder("Database Performance")
			try:
				db_service = services_manager.get[DB]("db")
				db_metrics = db_service.get_metrics()

				# Database stats cards
				db_stats_cards = [
					create_stat_card("Total Queries", db_metrics['total_queries'], icon="🗄️"),
					create_stat_card("Query Errors", db_metrics['errors'], icon="⚠️"),
					create_stat_card("Avg Query Time", f"{db_metrics['avg_query_time'] * 1000:.2f}ms", icon="⏱️"),
					create_stat_card("Active Connections", db_metrics['active_connections'], icon="🔌")
				]
				db_section.add_stats_cards(db_stats_cards, columns=4)

				# Database performance metrics table
				db_metrics_data = [{
					'metric': 'Average Query Time',
					'value': f"{db_metrics['avg_query_time'] * 1000:.2f}ms"
				}, {
					'metric': 'Minimum Query Time',
					'value': f"{db_metrics['min_query_time'] * 1000:.2f}ms"
				}, {
					'metric': 'Maximum Query Time',
					'value': f"{db_metrics['max_query_time'] * 1000:.2f}ms"
				}, {
					'metric': '95th Percentile',
					'value': f"{db_metrics['p95_query_time'] * 1000:.2f}ms"
				}, {
					'metric': '99th Percentile',
					'value': f"{db_metrics['p99_query_time'] * 1000:.2f}ms"
				}]

				db_table = TableBuilder(db_metrics_data)
				db_table.table["density"] = "compact"
				db_table.add_column("metric", "Metric", type="text")
				db_table.add_column("value", "Value", type="text")
				db_section.add_table(db_table)

				# SQL Query Patterns table
				if db_metrics.get('query_patterns'):
					query_patterns_data = []
					for pattern in db_metrics['query_patterns'][:20]:  # Top 20 queries
						query_patterns_data.append({
							'query': pattern['example_query'],
							'normalized': pattern['normalized_query'],
							'count': pattern['count'],
							'avg_time': f"{pattern['avg_time'] * 1000:.2f}ms",
							'total_time': f"{pattern['total_time'] * 1000:.2f}ms",
							'errors': pattern['error_count'],
							'params': pattern['example_params']
						})

					queries_table = TableBuilder(query_patterns_data)
					queries_table.table["density"] = "compact"
					queries_table.add_column("query", "Query", type="code", sortable=True, width="auto")
					queries_table.add_column("count", "Executions", type="number", sortable=True, width="100px")
					queries_table.add_column("avg_time", "Avg Time", type="text", sortable=True, width="100px")
					queries_table.add_column("total_time", "Total Time", type="text", sortable=True, width="100px")
					queries_table.add_column("errors", "Errors", type="number", sortable=True, width="80px")

					# Add row action to run EXPLAIN on query
					queries_table.add_row_action(
						id="explain-query",
						label="EXPLAIN",
						action=ActionBuilder().open_modal("explain-result", modal_data={
							"query": ValueRefBuilder.field("row", "query"),
							"params": ValueRefBuilder.field("row", "params")
						})
					)

					db_section.add_table(queries_table)

				page.add_section(db_section)
			except Exception as e:
				traceback.print_exception(e)
				# Database metrics not available, skip section
				pass

			# Model operations section
			model_section = SectionBuilder("Model Operations")
			try:
				# Import ABCModel to get metrics
				model_metrics = ABCModel.get_metrics()
				total_model_ops = ABCModel.get_total_operations()
				total_model_errors = ABCModel.get_total_errors()

				# Model stats cards
				model_stats_cards = [
					create_stat_card("Total Operations", total_model_ops, icon="📝"),
					create_stat_card("Operation Errors", total_model_errors, icon="❌"),
					create_stat_card("Active Models", len(model_metrics), icon="📊")
				]
				model_section.add_stats_cards(model_stats_cards, columns=3)

				# Model operations table
				model_ops_data = []
				for model_name, model_stats in model_metrics.items():
					for operation, count in model_stats['operations'].items():
						avg_time = model_stats['avg_times'].get(operation, 0)
						errors = model_stats['errors'].get(operation, 0)
						model_ops_data.append({
							'model': model_name,
							'operation': operation,
							'count': count,
							'avg_time': f"{avg_time * 1000:.2f}ms",
							'errors': errors
						})

				if model_ops_data:
					model_table = TableBuilder(model_ops_data)
					model_table.table["density"] = "compact"
					model_table.add_column("model", "Model", type="text", sortable=True)
					model_table.add_column("operation", "Operation", type="text", sortable=True)
					model_table.add_column("count", "Count", type="number", sortable=True)
					model_table.add_column("avg_time", "Avg Time", type="text", sortable=True)
					model_table.add_column("errors", "Errors", type="number", sortable=True)
					model_section.add_table(model_table)

					page.add_section(model_section)
			except Exception as e:
				# Model metrics not available, skip section
				pass

			# Add EXPLAIN modal for SQL query analysis
			page.add_modal("explain-result", ModalDefinition(
				title="EXPLAIN Query",
				size="large",
				closeOnOverlayClick=True,
				content=[
					create_defer(
						endpoint="/admin/database/explain",
						method="POST",
						trigger=create_defer_trigger_immediate(),
						body={
							"query": ValueRefBuilder.field("data", "query"),
							"params": ValueRefBuilder.field("data", "params")
						},
						loading_state=create_skeleton(variant="table", rows=3)
					)
				]
			))

			# Add real-time updates with polling for stats
			page.set_realtime(
				polling=PollingConfig(
					interval=2000,  # Poll every 2 seconds
					endpoint="/admin/metrics/stats",
					componentId="metrics-stats"
				)
			)

			return jsonify(page.build())

		except Exception as e:
			traceback.print_exc()
			page = PageBuilder(
				title="Metrics",
				description="Application metrics and monitoring"
			)
			error_section = SectionBuilder()
			#error_section.add_alert(
			#	f"Failed to load metrics: {str(e)}",
			#	variant="error"
			#)
			page.add_section(error_section)
			return jsonify(page.build())

	@register("/metrics/stats", methods=["GET"])
	@describe("Get metrics statistics for real-time updates", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_metrics_stats(self):
		services_manager = self.manager.get[Manager[ABCService]]("services")

		try:
			metrics_service = services_manager.get[NullMetrics]("metrics")

			if not metrics_service.ready:
				return jsonify({})

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

			error_rate_pct = stats['overview']['error_rate'] * 100

			# Build stats section
			stats_section = SectionBuilder()
			stats_section.set_id("metrics-stats")
			stats_section.add_stats_cards([
				create_stat_card("Total Requests", stats['overview']['total_requests'], icon="📊"),
				create_stat_card("Active Requests", stats['overview']['active_requests'], icon="⚡"),
				create_stat_card("Total Errors", stats['overview']['total_errors'], icon="❌"),
				create_stat_card("Error Rate", f"{error_rate_pct:.2f}%", icon="📈"),
				create_stat_card("Uptime", uptime_formatted, icon="⏱️")
			], columns=5)

			return jsonify(stats_section.build())

		except Exception as e:
			return jsonify({})

	@register("/api-keys", methods=["GET", "POST"])
	@describe("Get or create API keys", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def manage_api_keys(self):
		auth_plugin = self.manager.get[Auth]('plugins.auth')
		socketio = self.manager.get[NullSocketIO]("services.socketio")

		if request.method == "POST":
			data = request.get_json()
			level = data.get("level", 0)
			expire = data.get("expire")

			try:
				# Convert level to int if it's a string
				if isinstance(level, str):
					level = int(level)

				# Create the API key
				api_key = auth_plugin.create_apikey(level=level, expire=expire)

				# Emit Socket.IO event to refresh API keys page
				socketio.broadcast_to_page('api-keys', 'refresh_page', {})

				return jsonify({
					"message": "API key created successfully",
					"key": api_key,
					"level": level,
					"expire": expire
				}), 201
			except Exception as e:
				traceback.print_exc()
				return jsonify({"error": f"Failed to create API key: {str(e)}"}), 500

		# GET request - build DSL

		try:
			keys = auth_plugin.list_apikeys(limit=1000)

			# Convert to dict format, excluding the actual key value for security
			keys_data = []
			for key in keys:
				created_at = datetime.strptime(key.created_at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
				last_used = datetime.strptime(key.last_used, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp() if key.last_used else None
				keys_data.append({
					"id": key.id,
					"key_preview": f"{key.key[:8]}...{key.key[-4:]}" if len(key.key) > 12 else "***",
					"level": "Admin" if key.level == 1 else "User",
					"level_value": key.level,
					"expire": key.expire if key.expire else "Never",
					"created_at": int(created_at * 1000),
					"last_used": int(last_used * 1000) if last_used else None,
				})

			# Build DSL
			page = PageBuilder(
				title="API Keys",
				description="Manage API keys for programmatic access"
			)

			# API Keys table
			keys_section = SectionBuilder("API Keys")
			table = TableBuilder(keys_data)

			# Columns
			table.add_column("id", "ID", type="number", width="80px")
			table.add_column("key_preview", "Key", type="code")
			table.add_column("level", "Level")
			table.add_column("expire", "Expires")
			table.add_column("created_at", "Created", type="date")
			table.add_column("last_used", "Last Used", type="date")

			# Header action: Create API Key
			create_key_action = ActionBuilder()
			create_key_action.open_modal("create_key")
			table.add_header_action("create", "Create API Key", create_key_action)

			# Row action: Delete
			delete_action = ActionBuilder()
			delete_action.api_call(
				ValueRefBuilder.computed("/admin/api-keys/{id}", id=ValueRefBuilder.field("row", "id")),
				method="DELETE"
			).on_success(
				message="API key deleted successfully",
				action=ActionBuilder().refresh()
			)
			table.add_row_action(
				"delete",
				"Delete",
				delete_action,
				confirm_message=ValueRefBuilder.computed(
					"Delete API key {key_preview}? This cannot be undone.",
					key_preview=ValueRefBuilder.field("row", "key_preview")
				)
			)

			keys_section.add_table(table)
			page.add_section(keys_section)

			# Create API Key modal
			create_form = FormBuilder(
				submit_action=ActionBuilder().api_call("/admin/api-keys", method="POST", body={
					"level": ValueRefBuilder.field("form", "level"),
					"expire": ValueRefBuilder.field("form", "expire")
				}).on_success(
					action=ActionBuilder()
						.close_modal("create_key")
						.on_success(
							action=ActionBuilder().open_modal("key_created", modal_data={
								"key": ValueRefBuilder.field("response", "key")
							})
						)
				)
			)

			# Level field
			level_options = [
				FormFieldOption(value="0", label="User", description="Standard user access"),
				FormFieldOption(value="1", label="Admin", description="Full administrative access")
			]
			create_form.add_select_field("level", "Access Level", level_options, required=True, defaultValue="0")
			create_form.add_field("expire", "Expiration Date", type="datetime",
				helpText="Optional. Leave empty for a non-expiring key.")
			create_form.set_cancel_action(ActionBuilder().close_modal("create_key"))

			page.add_modal("create_key", ModalDefinition(
				title="Create API Key",
				size="medium",
				content=[create_form.build()],
				closeOnOverlayClick=True
			))

			# Key Created Success Modal
			key_success_alert = AlertComponent(
				type="alert",
				message="API Key Created Successfully! This key will only be shown once. Make sure to copy it now.",
				variant="success",
				dismissible=True
			)

			key_display = CodeBlockComponent(
				type="code-block",
				content=ValueRefBuilder.field("pageData", "key"),
				language="text",
				copyable=True
			)

			close_action = ActionBuilder().close_modal("key_created").on_success(action=ActionBuilder().refresh())
			close_button = ButtonComponent(
				type="button",
				label="Close",
				action=close_action.build(),
				variant="primary"
			)

			page.add_modal("key_created", ModalDefinition(
				title="API Key Created",
				size="medium",
				content=[key_success_alert, key_display],
				actions=[close_button],
				closeOnOverlayClick=False
			))

			# Add real-time updates
			page.set_realtime(
				socket_events=[
					SocketEventHandler(
						event="refresh_page",
						handler="refresh-page"
					)
				]
			)

			return jsonify(page.build())
		except Exception as e:
			traceback.print_exc()
			return jsonify({"title": "API Keys", "error": f"Failed to load API keys: {str(e)}"})

	@register("/api-keys/<int:key_id>", methods=["DELETE"])
	@describe("Delete an API key", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def delete_api_key(self, key_id: int):
		auth_plugin = self.manager.get[Auth]('plugins.auth')

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
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def reload_system(self):
		"""
		Reload system modules based on the 'target' parameter.

		Accepts JSON body with:
		- target: "all" | "services" | "plugins" | "apis" | specific module name
		"""
		socketio = self.manager.get[NullSocketIO]("services.socketio")
		services_manager = self.manager.get[Manager[ABCService]]("services")
		plugins_manager = self.manager.get[Manager[ABCPlugin]]("plugins")
		data = request.get_json() or {}
		target = data.get("target", "all")

		try:
			if target == "all":
				results = reload_all(current_app)
				socketio.broadcast_to_page('services', 'refresh_page', {})
				socketio.broadcast_to_page('overview', 'refresh_page', {})
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
				socketio.broadcast_to_page('services', 'refresh_page', {})
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
				elif target in self.manager._modules_specs:
					# For APIs, need to handle blueprints
					api_instance = self.manager._modules[target]
					unregister_blueprints(current_app, api_instance.blueprint.name)

					self.manager.reload(target)

					# Re-register blueprint
					new_instance = self.manager.get[ABCApi](target)
					current_app.register_blueprint(new_instance.blueprint)

					reloaded = True
					manager_name = "apis"

				if reloaded:
					if manager_name == "services":
						socketio.broadcast_to_page('services', 'refresh_page', {})
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

	@register("/dsl-showcase", methods=["GET"])
	@describe("Get DSL showcase page", "route")
	@cond(lambda self, **kwargs: True or self.auth.require_admin())
	def get_dsl_showcase(self):
		"""Return the comprehensive DSL showcase page"""
		from ._showcase import build_showcase_page
		return jsonify(build_showcase_page())

	@register("/webhooks", methods=["GET"])
	@describe("Get webhooks page")
	@cond(lambda self, *a, **kw: True or self.auth.require_admin())
	def get_webhooks(self):
		hooks = self.models.webhooks.get_all()
		events = self.models.webhooks.get_registered_events()
		events_data = [{"event": e} for e in events]

		return jsonify(PageBuilder("Webhooks")
			.add_section(SectionBuilder("Registered Events")
				.add_table(TableBuilder(events_data)
					.add_column("event", "Event", "text")
					.add_row_action(
						"fire",
						"Fire Event",
						icon="zap",
						action=ActionBuilder()
							.api_call("/admin/webhooks/fire-event", method="POST", body={"event": ValueRefBuilder.field("row", "event")})
							.on_success("Event fired")
					)
					.set_empty_state("No events registered", "Use @register_webhook decorator to register events")
				)
			)
			.add_section(SectionBuilder("Webhook Subscriptions")
				.add_table(TableBuilder(hooks or [])
					.add_column("id", "ID", "number")
					.add_column("event", "Event", "text")
					.add_column("url", "URL", "text")
					.add_column("enabled", "Enabled", "boolean")
					.add_column("last_used", "Last Used", "text")
					.add_column("trigger_count", "Triggers", "number")
					.add_column("last_error", "Last Error", "text")
					.add_header_action("add_webhook", "Add Webhook", icon="plus", action=ActionBuilder().open_modal("add-webhook"))
					.add_row_action(
						"toggle",
						"Toggle",
						icon="toggle-left",
						action=ActionBuilder()
							.api_call("/admin/webhooks/toggle", method="POST", body={"id": ValueRefBuilder.field("row", "id")})
							.on_success("Webhook toggled", ActionBuilder().refresh())
					)
					.add_row_action(
						"test",
						"Test URL",
						icon="play",
						action=ActionBuilder()
							.api_call("/admin/webhooks/test", method="POST", body={"id": ValueRefBuilder.field("row", "id")})
							.on_success("Test request sent")
					)
					.add_row_action(
						"delete",
						"Delete",
						icon="trash",
						confirm_message="Are you sure you want to delete this webhook?",
						action=ActionBuilder()
							.api_call("/admin/webhooks/delete", method="POST", body={"id": ValueRefBuilder.field("row", "id")})
							.on_success("Webhook deleted", ActionBuilder().refresh())
					)
					.set_empty_state("No webhooks configured", "Add a webhook to receive notifications when events occur")
				)
			).add_modal("add-webhook", ModalBuilder("Add a new Webhook")
				.add_component(FormBuilder(
					ActionBuilder()
						.api_call("/admin/webhooks/add", method="POST", body={
							"event": ValueRefBuilder.field("form", "event"),
							"url": ValueRefBuilder.field("form", "url"),
							"headers": ValueRefBuilder.field("form", "headers"),
							"body": ValueRefBuilder.field("form", "body"),
							"enabled": ValueRefBuilder.field("form", "enabled")
						})
						.on_success("Webhook created", ActionBuilder().close_modal("add-webhook").refresh())
				)
					.add_select_field("event", "Event", options=[FormFieldOption(value=event, label=event, description="") for event in events], required=True)
					.add_field("url", "URL", type="text", required=True, placeholder="https://example.com/webhook")
					.add_field("headers", "Headers (JSON)", type="textarea", required=False, placeholder='{"Authorization": "Bearer token"}')
					.add_field("body", "Body Template (JSON)", type="textarea", required=False, placeholder='{"event": "{{event}}", "data": "{{data}}"}')
					.add_field("enabled", "Enabled", type="checkbox", defaultValue=True)
					.set_cancel_action(ActionBuilder().close_modal("add-webhook"))
				.build())
			).build())

	@register("/webhooks/fire-event", methods=["POST"])
	@describe("Fire a webhook event", method="POST")
	@cond(lambda self, *a, **kw: True or self.auth.require_admin())
	def fire_webhook_event(self):
		data = request.get_json()
		event = data.get("event")

		if not event:
			return jsonify({"error": "Event name is required"}), 400

		from ..plugins.models.webhook import Webhook
		Webhook.fire(event, {"test": True, "message": "Test event fired from admin panel"})

		return jsonify({"success": True, "message": f"Event '{event}' fired"})

	@register("/webhooks/add", methods=["POST"])
	@describe("Add a new webhook", method="POST")
	@cond(lambda self, *a, **kw: True or self.auth.require_admin())
	def add_webhook(self):
		data = request.get_json()
		event = data.get("event")
		url = data.get("url")
		headers_str = data.get("headers", "{}")
		body_str = data.get("body", "{}")
		enabled = data.get("enabled", True)

		if not event or not url:
			return jsonify({"error": "Event and URL are required"}), 400

		try:
			headers = json.loads(headers_str) if headers_str else {}
		except json.JSONDecodeError:
			return jsonify({"error": "Invalid JSON in headers"}), 400

		try:
			body = json.loads(body_str) if body_str else {}
		except json.JSONDecodeError:
			return jsonify({"error": "Invalid JSON in body template"}), 400

		webhook_id = self.models.webhooks.create(
			url=url,
			event=event,
			headers=headers,
			body=body,
			enabled=enabled
		)

		return jsonify({"success": True, "id": webhook_id})

	@register("/webhooks/toggle", methods=["POST"])
	@describe("Toggle webhook enabled state", method="POST")
	@cond(lambda self, *a, **kw: True or self.auth.require_admin())
	def toggle_webhook(self):
		data = request.get_json()
		webhook_id = data.get("id")

		if not webhook_id:
			return jsonify({"error": "Webhook ID is required"}), 400

		webhook = self.models.webhooks.get(int(webhook_id))
		if not webhook:
			return jsonify({"error": "Webhook not found"}), 404

		new_state = not webhook.get("enabled", True)
		self.models.webhooks.update(int(webhook_id), enabled=new_state)

		return jsonify({"success": True, "enabled": new_state})

	@register("/webhooks/delete", methods=["POST"])
	@describe("Delete a webhook", method="POST")
	@cond(lambda self, *a, **kw: True or self.auth.require_admin())
	def delete_webhook(self):
		data = request.get_json()
		webhook_id = data.get("id")

		if not webhook_id:
			return jsonify({"error": "Webhook ID is required"}), 400

		deleted = self.models.webhooks.delete(int(webhook_id))
		if not deleted:
			return jsonify({"error": "Webhook not found"}), 404

		return jsonify({"success": True})

	@register("/webhooks/test", methods=["POST"])
	@describe("Test a webhook by sending a test request to its URL", method="POST")
	@cond(lambda self, *a, **kw: True or self.auth.require_admin())
	def test_webhook(self):
		data = request.get_json()
		webhook_id = data.get("id")

		if not webhook_id:
			return jsonify({"error": "Webhook ID is required"}), 400

		webhook = self.models.webhooks.get(int(webhook_id))
		if not webhook:
			return jsonify({"error": "Webhook not found"}), 404

		# Send test request directly to the webhook URL
		import requests as http_requests
		from datetime import datetime, timezone

		test_payload = {
			"event": webhook["event"],
			"data": {"test": True, "webhook_id": webhook_id, "message": "Test webhook from admin panel"},
			"timestamp": datetime.now(timezone.utc).isoformat() + "Z"
		}

		headers = webhook.get("headers", {})
		if "Content-Type" not in headers:
			headers["Content-Type"] = "application/json"

		try:
			response = http_requests.post(
				webhook["url"],
				json=test_payload,
				headers=headers,
				timeout=10
			)
			return jsonify({
				"success": True,
				"status_code": response.status_code,
				"message": f"Test request sent to {webhook['url']}"
			})
		except http_requests.RequestException as e:
			return jsonify({"error": f"Request failed: {str(e)}"}), 500

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
