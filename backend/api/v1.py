from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from ._base_api import ABCApi, describe, register
from ._manager import Manager
from flask import Blueprint, request
from ..services.db import Service as DB


class V1API(ABCApi):
	def __init__(self, manager: Manager[ABCApi], base: ABCApi):
		self.manager = manager
		self.base = base
		self.bp = self.create_blueprint("v1", parent=base, url_prefix="/v1")
		self.db = self.manager.get[DB]('services.db')

		self.add_rules(self.bp)

	@register("/sql")
	@describe(
		"endpoint to test some sql queries", "route",
		params={
			"query": {
				"type": "string",
				"required": True,
				"description": "The sqlite query to run",
				"in": "query",
			}
		}
	)
	def sql(self):
		query = request.args.get("query", "")
		with self.db() as cursor:
			result = cursor.execute(query).fetchall()
		return {"result": result}

	@register("/")
	@describe("Returns API version information")
	def index(self):
		"""V1 API index with version details and available endpoints."""
		return {"version": "1.0", "endpoints": ["/hello", "/test"]}

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
