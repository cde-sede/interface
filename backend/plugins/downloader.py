from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from urllib.parse import urlparse
from collections.abc import Callable
from ._base_plugin import ABCPlugin
from ._manager import Manager
from .models import ABCModel, File
from ..services.tasks import Service as Tasks
from .models.webhook import register_webhook
import requests

import time

class Downloader(ABCPlugin):
	def __init__(self, manager: Manager[ABCPlugin]):
		self.manager = manager

		tasks = manager.get[Tasks]("services.tasks")

		# Register the static method (no closure over self)
		tasks.register(name="download", timeout=30.0)(self.download_task)

	@property
	def name(self) -> str:
		return "downloader"

	@register_webhook("downloader.test")
	def test(*a, **kw):
		return "Lol"

	@staticmethod
	def download_task(url: str) -> dict:
		"""
		Task function executed in worker process.
		Must be static to avoid closure issues.
		"""
		# Reinitialize manager in worker context
		from backend.plugins import manager as plugin_manager

		# Get downloader plugin instance
		downloader = plugin_manager.get('downloader')

		# Call instance method
		return downloader.download(url)

	def download(self, url: str) -> dict:
		"""Helper method called by task."""
		import time
		print("DOWNLOAD")
		time.sleep(5)
		print("DONE!")
		return {"result": "OK"}

		#resp = requests.head(url, allow_redirects=True, timeout=10)
		#headers = resp.headers
		#return dict(headers)

def setup(manager: Manager[ABCPlugin], /):
	require("model")
	require("models.webhook")
	return Downloader(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)

