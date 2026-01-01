from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from _injected import *

from flask import Blueprint, jsonify, request, current_app
from ._base_api import ABCApi, describe, register, cond
from ._manager import Manager
from ..plugins.auth import AuthUtils, Plugin as Auth
from ..plugins._base_plugin import ABCPlugin

from ..services.socketio import Service as SocketIOService
from flask_socketio import join_room, leave_room

from ._dsl_builder import *
from ._dsl_types import *

import time


class API(ABCApi):
	def __init__(self, manager: Manager[ABCApi]):
		self.manager = manager
		self.bp = self.create_blueprint("content", url_prefix="/content")

		self.add_rules(self.bp)
		self._register_socketio()

	def _register_socketio(self):
		socketio = self.manager.get[SocketIOService]("services.socketio")
		socketio.emit("content", {}, "refresh_page")

		@socketio.on("home")
		def handle_join():
			join_room("content")



	@property
	def isroot(self) -> bool:
		return True

	@property
	def name(self) -> str:
		return "content"

	@property
	def blueprint(self) -> Blueprint:
		return self.bp


	@register("/img/<string:data>", methods=["GET"])
	@describe("Deferred image grid endpoint")
	def get_img(self, data):
		return jsonify([
		])

	@register("/grid/<string:page>", methods=["GET"])
	@describe("Defered grid")
	def get_grid(self, page):
		if page == "infinite":
			index = int(request.args.get("index", 0))
			count = int(request.args.get("count", 9))
			return jsonify([
				create_grid(
					[ CardBuilder(f"{page}:{index + i}").build() for i in range(count) ],
					columns='repeat(auto-fill, minmax(140px, 1fr))'
				),
				create_defer(
					"/content/grid/infinite",
					trigger=create_defer_trigger_intersection(),
					loading_state= create_grid(
						[ SkeletonBuilder("rectangular").build() for i in range(count) ],
						columns='repeat(auto-fill, minmax(140px, 1fr))'
					),
					params={"index": index + count, "count": count}
				)
			])
		return jsonify([
			create_grid([
				CardBuilder(f"{page}:{i}").build()
				for i in range(27)
			], columns='repeat(auto-fill, minmax(140px, 1fr))'),
		])

	@register("/table/<string:kind>", methods=["GET"])
	def get_table(self, kind):
		if kind == "table":
			return jsonify([TableBuilder([])
				.id("data_table")
				.add_column("id", "ID", type="text", width="80px", sortable=True)
				.build(),
				create_defer("/content/table/0", trigger=create_defer_trigger_immediate())
			])
		return jsonify([
			create_defer(f"/content/table/{int(kind) + 1}", trigger=create_defer_trigger_intersection(),
				on_trigger=ActionBuilder().add_rows("data_table", ValueRefBuilder.literal([{"id": kind}]))
			)
		])

	@register("/home", methods=["GET"])
	@describe("The main app page")
	def get_home(self):
		return jsonify(PageBuilder(
			title="", description=""
		).add_section(
			SectionBuilder()
			.add_component(create_defer(
				"/content/table/table",
				trigger=create_defer_trigger_immediate(),
			))
		).build())


def setup(manager: Manager[ABCApi], /):
	return API(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)
