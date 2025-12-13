from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from urllib.parse import urlparse
from collections.abc import Callable
from ._base_plugin import ABCPlugin
from ._manager import Manager
from .models import ABCModel, File
from ..services.tasks import Service as Tasks
import requests

class Downloader(ABCPlugin):
	def __init__(self, manager: Manager[ABCPlugin]):
		self.manager = manager

		tasks = manager.get[Tasks]("services.tasks")

		@tasks.register(name="download", timeout=30.0)
		def download(url):
			import time
			print("Task start")
			time.sleep(5)
			print("Task end")

	@property
	def name(self) -> str:
		return "downloader"

	def download(self, url: str):
		resp = requests.head(url, allow_redirects=True, timeout=10)
		headers = resp.headers
		return dict(headers)

def setup(manager: Manager[ABCPlugin], /):
	return Downloader(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)

