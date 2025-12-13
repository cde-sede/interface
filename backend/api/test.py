from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from ._base_api import ABCApi, describe, register, cond
from ._manager import Manager
from flask import Blueprint, request, jsonify
from ..plugins.auth import AuthUtils
from ..plugins.downloader import Downloader


class TestAPI(ABCApi):
	def __init__(self, manager: Manager[ABCApi], parent: ABCApi):
		self.bp = self.create_blueprint("test", parent=parent, url_prefix="/test")
		self.manager = manager

		self.downloader = self.manager.get[Downloader]('plugins.downloader')
		self.add_rules(self.bp)

	@cond(AuthUtils.require_auth)
	@register("/index")
	@describe("Tests cond", "route")
	def index(self):
		return {"result": "hello, world!"}

	@register("/download/<path:url>")
	@describe("Tests cond", "route",
		params={
			"url": {
				"type": "string",
				"required": True,
				"description": "The URL to download",
				"in": "path"
			}
		}
	)
	def download(self, url):
		return self.downloader.download(url)

	@property
	def name(self) -> str:
		return "test"

	@property
	def blueprint(self) -> Blueprint:
		return self.bp


def setup(manager: Manager[ABCApi], /):
	parent = require('v1')
	return TestAPI(manager, parent)

if TYPE_CHECKING:
	setup = validate_setup(setup)
