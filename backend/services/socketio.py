"""
Socket.IO service for real-time bidirectional communication.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Any, Dict, Optional
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup
	from .logs import Service as Logs

from flask import Flask, request as flask_request
from flask_socketio import SocketIO, join_room, leave_room, disconnect
from functools import wraps
import threading

from ._base_service import ABCService
from ._manager import Manager
from .settings import Service as Settings
from ..plugins.auth import Plugin as AuthPlugin


class Service(ABCService):
	"""Socket.IO service for real-time bidirectional communication."""

	def __init__(self, manager: Manager[ABCService]):
		self.manager = manager
		self._auth_plugin: Optional[AuthPlugin] = None
		self._settings: Optional[Settings] = None
		self._logs: Optional[Logs] = None

		self._handlers: Dict[str, Dict[str, Any]] = {}
		self._handler_lock = threading.Lock()

		self.app: Flask = None # pyright: ignore
		self.sio: Optional[SocketIO] = None

		self._sessions: Dict[str, Dict[str, Any]] = {}
		self._sessions_lock = threading.Lock()

		self._ready = False

	@property
	def settings(self) -> Settings:
		if self._settings is None or not self._settings.ready:
			self._settings = self.manager.get[Settings]('settings')
		return self._settings

	@property
	def auth_plugin(self) -> AuthPlugin:
		if self._auth_plugin is None:
			self._auth_plugin = self.manager.get[AuthPlugin]('plugins.auth')
		return self._auth_plugin

	@property
	def logs(self):
		if self._logs is None or not self._logs.ready:
			from .logs import Service as Logs
			self._logs = self.manager.get[Logs]('logs')
		return self._logs

	@property
	def name(self) -> str:
		return "socketio"

	@property
	def ready(self) -> bool:
		return self._ready

	def initialize(self, app: Flask):
		"""Initialize Socket.IO with Flask app."""
		self.logs.info("Initializing Socket.IO service", service="socketio",
		              cors_origins=self.settings.socketio_cors_origins)

		self.app = app

		# Build Redis URL for cross-process messaging
		redis_url = self._build_redis_url()

		self.logs.info("Configuring Socket.IO with Redis message queue",
		              service="socketio", redis_url=redis_url.replace(self.settings.redis_password or '', '***'))

		self.sio = SocketIO(
			app,
			cors_allowed_origins=self.settings.socketio_cors_origins,
			ping_timeout=self.settings.socketio_ping_timeout,
			ping_interval=self.settings.socketio_ping_interval,
			async_mode='threading',
			message_queue=redis_url,  # Enable cross-process messaging
			logger=False,
			engineio_logger=False
		)

		self.sio.on_event('connect', self._handle_connect)
		self.sio.on_event('disconnect', self._handle_disconnect)

		self._register_all_handlers()

		self._ready = True
		self.logs.info("Socket.IO service initialized successfully", service="socketio")

	def initialize_worker(self):
		"""Initialize Socket.IO for worker subprocess (emit-only, no Flask app)."""
		self.logs.info("Initializing Socket.IO for worker subprocess", service="socketio")

		self.app = None

		# Build Redis URL for cross-process messaging
		redis_url = self._build_redis_url()

		self.logs.info("Configuring Socket.IO with Redis message queue (worker mode)",
		              service="socketio", redis_url=redis_url.replace(self.settings.redis_password or '', '***'))

		# Create SocketIO instance without Flask app, just for emitting via Redis
		self.sio = SocketIO(message_queue=redis_url, logger=False, engineio_logger=False)

		self._ready = True
		self.logs.info("Socket.IO service initialized for worker", service="socketio")

	def _build_redis_url(self) -> str:
		"""Build Redis URL for message queue."""
		redis_url = (
			f"redis://"
			f"{self.settings.redis_host}:"
			f"{self.settings.redis_port}/"
			f"{self.settings.redis_db}"
		)
		if self.settings.redis_password:
			redis_url = (
				f"redis://:{self.settings.redis_password}@"
				f"{self.settings.redis_host}:"
				f"{self.settings.redis_port}/"
				f"{self.settings.redis_db}"
			)
		return redis_url

	def _handle_connect(self, auth):
		"""Handle client connection with optional JWT authentication."""
		try:
			# Get token from query params or auth dict
			token = flask_request.args.get('token')
			if not token and auth and isinstance(auth, dict):
				token = auth.get('token')

			session_id = flask_request.sid

			if token:
				user_data = self.auth_plugin.verify_token(token)
				if user_data:
					with self._sessions_lock:
						self._sessions[session_id] = {
							'user_id': user_data.id,
							'username': user_data.username,
							'email': user_data.email,
							'authenticated': True
						}

					join_room(f"user_{user_data.id}")
					self.logs.info("Client connected with authentication", service="socketio",
					             session_id=session_id, user_id=user_data.id,
					             username=user_data.username)
					return True

			with self._sessions_lock:
				self._sessions[session_id] = {'authenticated': False}

			self.logs.debug("Client connected without authentication", service="socketio",
			               session_id=session_id)
			return True
		except Exception as e:
			self.logs.error(f"Socket.IO connection error", service="socketio", error=str(e))
			return False

	def _handle_disconnect(self, *args):
		"""Cleanup session data and leave rooms."""
		session_id = flask_request.sid

		with self._sessions_lock:
			session_data = self._sessions.pop(session_id, None)

		if session_data and session_data.get('authenticated'):
			user_id = session_data.get('user_id')
			username = session_data.get('username')
			if user_id:
				leave_room(f"user_{user_id}")
			self.logs.info("Authenticated client disconnected", service="socketio",
			             session_id=session_id, user_id=user_id, username=username)
		else:
			self.logs.debug("Client disconnected", service="socketio",
			               session_id=session_id)

	def get_current_user(self) -> Optional[Dict[str, Any]]:
		"""Get current user data from session."""
		session_id = flask_request.sid
		with self._sessions_lock:
			session_data = self._sessions.get(session_id)

		if session_data and session_data.get('authenticated'):
			return session_data
		return None

	def on(self, event: str, authenticated: bool = False):
		"""
		Decorator to register Socket.IO event handlers.

		Args:
			event: Event name to listen for
			authenticated: If True, require JWT authentication
		"""
		def decorator(func: Callable) -> Callable:
			@wraps(func)
			def wrapper(*args, **kwargs):
				if authenticated:
					user = self.get_current_user()
					if not user:
						disconnect()
						return {'error': 'Authentication required'}
				return func(*args, **kwargs)

			with self._handler_lock:
				self._handlers[event] = {
					'handler': wrapper,
					'authenticated': authenticated,
					'original': func
				}

			if self.sio:
				self.sio.on_event(event, wrapper)

			self.logs.debug(f"Registered Socket.IO event handler", service="socketio",
			               event=event, authenticated=authenticated)

			return func

		return decorator

	def _register_all_handlers(self):
		"""Register all handlers with SocketIO instance."""
		with self._handler_lock:
			for event, handler_info in self._handlers.items():
				self.sio.on_event(event, handler_info['handler'])

	def emit(self, event: str, data: Any, room: Optional[str] = None, namespace: str = '/'):
		"""
		Emit event to clients.

		Args:
			event: Event name
			data: Data to send (JSON-serializable)
			room: Room to emit to (None = all clients)
			namespace: Socket.IO namespace
		"""
		if not self.sio:
			return

		# When using Redis message queue, emit works without Flask context
		# This allows worker subprocesses to emit events
		if self.app:
			with self.app.app_context():
				self.sio.emit(event, data, room=room, namespace=namespace)
		else:
			# Worker subprocess - emit directly (Redis handles cross-process)
			self.sio.emit(event, data, room=room, namespace=namespace)

	def emit_to_user(self, user_id: int, event: str, data: Any):
		"""Emit event to a specific user."""
		room = self.get_user_room(user_id)
		self.emit(event, data, room=room)

	def broadcast(self, event: str, data: Any):
		"""Broadcast event to all connected clients."""
		self.emit(event, data, room=None)

	def broadcast_to_page(self, page: str, event: str, data: Any):
		"""Broadcast event to all clients viewing a specific page."""
		room_name = f"page_{page}"
		self.emit(event, data, room=room_name)

	def join_custom_room(self, room_name: str):
		"""Join a custom room."""
		join_room(room_name)

	def leave_custom_room(self, room_name: str):
		"""Leave a custom room."""
		leave_room(room_name)

	def get_user_room(self, user_id: int) -> str:
		"""Get room name for a specific user."""
		return f"user_{user_id}"


class NullSocketIO(ABCService):
	"""Null Socket.IO service when disabled."""

	def __init__(self):
		self._ready = True

	def initialize(self, app: Flask):
		pass

	def emit(self, *args, **kwargs):
		pass

	def emit_to_user(self, *args, **kwargs):
		pass

	def broadcast(self, *args, **kwargs):
		pass

	def broadcast_to_page(self, *args, **kwargs):
		pass

	def on(self, event: str, authenticated: bool = False):
		def decorator(func: Callable) -> Callable:
			return func
		return decorator

	def get_current_user(self) -> Optional[Dict[str, Any]]:
		return None

	def join_custom_room(self, room_name: str):
		pass

	def leave_custom_room(self, room_name: str):
		pass

	def get_user_room(self, user_id: int) -> str:
		return f"user_{user_id}"

	@property
	def name(self) -> str:
		return "socketio"

	@property
	def ready(self) -> bool:
		return self._ready


def setup(manager: Manager[ABCService], /):
	require('settings')
	require('logs')
	settings = manager.get[Settings]('settings')

	if settings.socketio_enabled:
		return Service(manager)
	else:
		return NullSocketIO()


if TYPE_CHECKING:
	setup = validate_setup(setup)
