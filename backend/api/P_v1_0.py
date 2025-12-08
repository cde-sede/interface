from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from _injected import *

from .base_api import ABCApi, describe
from .manager import Manager
from flask import Blueprint


class V1API(ABCApi):
	def __init__(self, manager: Manager[ABCApi], base: ABCApi):
		self.manager = manager
		self.base = base
		self.bp = self.create_blueprint("v1", parent=base, url_prefix="/v1")

		# Add routes to v1 API
		self.bp.add_url_rule("/", view_func=self.index)
		self.bp.add_url_rule("/hello", view_func=self.hello)
		self.bp.add_url_rule("/test", view_func=self.test_view)

	@describe("Returns API version information")
	def index(self):
		"""V1 API index with version details and available endpoints."""
		return {"version": "1.0", "endpoints": ["/hello", "/test"]}

	@describe("Simple greeting endpoint")
	def hello(self):
		"""Returns a friendly greeting message from the V1 API."""
		return {"message": "Hello from API v1!"}

	@describe("Returns test data")
	def test_view(self):
		"""Test endpoint that returns sample data for debugging."""
		return {"foo": "bar"}

	@property
	def name(self) -> str:
		return "v1"

	@property
	def blueprint(self) -> Blueprint:
		return self.bp


def setup(manager: Manager[ABCApi], /):
	base = require('module_api_0')
	return V1API(manager, base)

if TYPE_CHECKING:
	setup = validate_setup(setup)
