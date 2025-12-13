from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup

from ._base_api import ABCApi, describe, register, cond
from ._manager import Manager
from flask import Blueprint, request, jsonify, Response
from ..plugins.auth import AuthUtils
from ..services.prometheus import NullPrometheus, generate_latest
from ..services.metrics import NullMetrics


class PrometheusAPI(ABCApi):
	def __init__(self, manager: Manager[ABCApi], parent: ABCApi):
		self.bp = self.create_blueprint("stats", parent=parent, url_prefix="/stats")
		self.manager = manager
		self._prometheus = manager.get[NullPrometheus]("services.prometheus")
		self._metrics = manager.get[NullMetrics]("services.metrics")
		

		self.add_rules(self.bp)

	#@cond(AuthUtils.require_auth)
	@register("/prometheus")
	@describe("Get prometheus metrics", "route")
	def prometheus(self):
		return Response(generate_latest(self._prometheus.get_registry()), mimetype='text/plain')

	@register("/metrics")
	@describe("Get prometheus metrics", "route")
	def metrics(self):
		return self._metrics.get_stats()


	@property
	def name(self) -> str:
		return "metrics-api"

	@property
	def blueprint(self) -> Blueprint:
		return self.bp


def setup(manager: Manager[ABCApi], /):
	parent = require('v1')
	return PrometheusAPI(manager, parent)

if TYPE_CHECKING:
	setup = validate_setup(setup)
