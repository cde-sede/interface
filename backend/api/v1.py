from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from ._base_api import ABCApi, describe
from ._manager import Manager
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
		self.bp.add_url_rule("/greet/<name>", view_func=self.greet)

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

	@describe(
		"Personalized greeting with optional formality",
		params={
			"name": {
				"type": "string",
				"required": True,
				"description": "The name of the person to greet",
				"in": "path"
			},
			"formal": {
				"type": "boolean",
				"required": False,
				"description": "Use formal greeting",
				"in": "query"
			}
		}
	)
	def greet(self, name):
		"""Returns a personalized greeting message."""
		from flask import request
		formal = request.args.get('formal', 'false').lower() == 'true'
		greeting = f"Good day, {name}" if formal else f"Hey, {name}!"
		return {"message": greeting}

	@property
	def name(self) -> str:
		return "v1"

	@property
	def blueprint(self) -> Blueprint:
		return self.bp


def setup(manager: Manager[ABCApi], /):
	base = require('api')
	return V1API(manager, base)

if TYPE_CHECKING:
	setup = validate_setup(setup)
