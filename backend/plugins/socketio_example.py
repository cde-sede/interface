"""
Example Socket.IO plugin demonstrating event handlers.
"""
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from . import ABCPlugin
from ..manager import Manager
import time


class Plugin(ABCPlugin):
	def __init__(self, manager: Manager[ABCPlugin]):
		self.manager = manager
		self._socketio = None

	@property
	def socketio(self):
		if self._socketio is None:
			self._socketio = self.manager.get('services.socketio')
		return self._socketio

	@property
	def name(self) -> str:
		return "socketio_example"

	def register_handlers(self):
		"""Register Socket.IO event handlers."""

		@self.socketio.on('echo')
		def handle_echo(data):
			"""Public echo event - no auth required."""
			message = data.get('message', '')
			print(f"[Echo] {message}")
			self.socketio.broadcast('echo_response', {
				'message': message,
				'timestamp': time.time()
			})
			return {'status': 'echoed'}

		@self.socketio.on('private_message', authenticated=True)
		def handle_private(data):
			"""Authenticated private message."""
			user = self.socketio.get_current_user()
			message = data.get('message', '')

			print(f"[Private] User {user['user_id']}: {message}")

			self.socketio.emit_to_user(
				user['user_id'],
				'private_response',
				{
					'message': f"Received: {message}",
					'user': user['username']
				}
			)
			return {'status': 'sent'}


def setup(manager: Manager[ABCPlugin], /):
	plugin = Plugin(manager)
	plugin.register_handlers()
	return plugin


if TYPE_CHECKING:
	setup = validate_setup(setup)
