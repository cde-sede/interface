from flask import Flask, jsonify, send_from_directory, abort
from flask_cors import CORS
from pathlib import Path
import os
import atexit

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

#from .plugins import manager
#for plugin_name in manager.list_plugins():
#	manager.load(plugin_name)
#	print(f'{plugin_name=}')
#
#print(manager.get('module_example_0').name)

def load_apis():
	from .api import manager, ABCApi
	for api in manager.list_plugins(): manager.load(api)

	root = manager.get("api")
	assert isinstance(root, ABCApi)

	app.register_blueprint(root.blueprint)

def load_services():
	from .services import manager
	for service in manager.list_plugins(): manager.load(service)

	manager.get("prometheus").initialize(app)
	manager.get("metrics").initialize(app)

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

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
	if path and app.static_folder and (Path(app.static_folder) / path).exists():
		return send_from_directory(app.static_folder, path)
	elif app.static_folder:
		return send_from_directory(app.static_folder, 'index.html')
	else:
		abort(404)

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=5000)
