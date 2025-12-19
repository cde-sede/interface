from flask import Flask, jsonify, send_from_directory, abort
from flask_cors import CORS
from pathlib import Path
import os
import atexit
from werkzeug.routing import Rule

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

def load_apis():
	from .api import manager, ABCApi
	for api in manager.list_plugins(): manager.load(api)

	app.register_blueprint(manager.get[ABCApi]("api").blueprint)
	app.register_blueprint(manager.get[ABCApi]("admin").blueprint)

def load_services():
	from .services import manager, ABCService
	for service in manager.list_plugins(): manager.load(service)

	from .services.prometheus import NullPrometheus
	from .services.metrics import NullMetrics
	from .services.socketio import NullSocketIO

	manager.get[NullPrometheus]("prometheus").initialize(app)
	manager.get[NullMetrics]("metrics").initialize(app)
	manager.get[NullSocketIO]("socketio").initialize(app)

def load_plugins():
	from .plugins import manager
	for plugin in manager.list_plugins(): manager.load(plugin)

load_services()
load_plugins()
load_apis()

# Register task worker shutdown handler
def shutdown_task_workers():
	"""Gracefully shutdown task workers on app exit"""
	try:
		from .services import manager
		tasks = manager.get("tasks")
		if tasks and tasks.workers_enabled:
			tasks._stop_workers()
	except:
		pass  # Ignore errors during shutdown

atexit.register(shutdown_task_workers)

@app.teardown_appcontext
def teardown_workers(exception=None):
	"""Flask teardown handler for task workers"""
	# Only stop workers if this is the final teardown
	# In WSGI environments, teardown happens per-request, so we skip it
	pass


@app.route('/api/health', methods=['GET'])
def health():
	return jsonify({'status': 'ok', 'message': 'Backend is running'})

@app.route('/api/hello', methods=['GET'])
def hello():
	return jsonify({'message': 'Hello from Flask!'})

@app.errorhandler(404)
def not_found(e):
	"""
	Handle 404 errors by serving the React app for non-API routes.
	This allows React Router to handle client-side routing.
	"""
	from flask import request

	path = request.path.rstrip('/')

	# If it's an API endpoint with sub-paths (e.g., /api/v1/users, /admin/menu),
	# return JSON 404
	if (path.startswith('/api/') and path.count('/') > 1) or \
	   (path.startswith('/admin/') and path.count('/') > 1):
		return jsonify({'error': 'Not found'}), 404

	# For all other routes (including /admin, /docs), serve the React app (SPA)
	if app.static_folder:
		return send_from_directory(app.static_folder, 'index.html')
	else:
		abort(404)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
	# Serve static files (JS, CSS, images, etc.)
	if path and app.static_folder and (Path(app.static_folder) / path).exists():
		return send_from_directory(app.static_folder, path)

	# For all other paths (including /admin, /docs), serve index.html
	# Let React Router handle the routing
	elif app.static_folder:
		return send_from_directory(app.static_folder, 'index.html')
	else:
		abort(404)

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=5000)
