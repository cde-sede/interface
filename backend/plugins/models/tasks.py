"""
Task model for background task execution system.
"""
from typing import TYPE_CHECKING
import time
import json

if TYPE_CHECKING:
	from backend.manager import Manager
	from backend.plugins import ABCPlugin

from backend.plugins.models._model import ABCModel
import json



class Task(ABCModel):
	"""
	Task model for persisting background task state.

	Stores task metadata, parameters, results, and execution status
	in SQLite database for durability across server restarts.
	"""

	class TaskStatus:
		"""Task status constants"""
		PENDING = "pending"
		RUNNING = "running"
		COMPLETED = "completed"
		FAILED = "failed"
		TIMEOUT = "timeout"


	class TaskPriority:
		"""Task priority levels"""
		LOW = -10
		NORMAL = 0
		HIGH = 10
		CRITICAL = 100


	@property
	def name(self) -> str:
		return "tasks"

	def ensure(self) -> None:
		"""Create tasks table and indexes if they don't exist"""
		with self.db() as db:
			db.execute("""
				CREATE TABLE IF NOT EXISTS tasks (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					name TEXT NOT NULL,
					status TEXT NOT NULL,
					priority INTEGER NOT NULL DEFAULT 0,
					timeout REAL,
					params TEXT,
					result TEXT,
					error TEXT,
					traceback TEXT,
					created_at REAL NOT NULL,
					started_at REAL,
					completed_at REAL,
					worker_id TEXT,
					is_async BOOLEAN DEFAULT 0,
					module TEXT,
					qualname TEXT
				)
			""")

			# Create indexes for performance
			db.execute("""
				CREATE INDEX IF NOT EXISTS idx_tasks_status
				ON tasks(status)
			""")

			db.execute("""
				CREATE INDEX IF NOT EXISTS idx_tasks_priority
				ON tasks(priority DESC, created_at ASC)
			""")

	def create(self, name: str, params: dict | None = None, priority: int = 0, timeout: float | None = None,
			   module: str | None = None, qualname: str | None = None, is_async: bool = False) -> int:
		"""
		Insert new task record.

		Args:
			name: Task function name
			params: Task parameters (will be JSON serialized)
			priority: Task priority (higher = more important)
			timeout: Max execution time in seconds (None = no timeout)
			module: Task function module path (for worker process import)
			qualname: Task function qualified name (for worker process import)
			is_async: Whether task function is async

		Returns:
			task_id: Database ID of created task
		"""
		params_json = json.dumps(params) if params else None
		created_at = time.time()

		with self.db() as db:
			cursor = db.execute("""
				INSERT INTO tasks (name, status, priority, timeout, params, created_at, module, qualname, is_async)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
			""", (name, Task.TaskStatus.PENDING, priority, timeout, params_json, created_at, module, qualname, is_async))

			assert cursor.lastrowid is not None
			return cursor.lastrowid

	def update(self, task_id: int, **kwargs) -> None:
		"""
		Update task fields. Automatically JSON-serializes the 'result' field.

		Args:
			task_id: Task ID to update
			**kwargs: Fields to update (status, result, error, traceback, started_at, completed_at, worker_id)
		"""
		if not kwargs:
			return

		# Handle result field - serialize to JSON if needed
		if 'result' in kwargs and kwargs['result'] is not None:
			result = kwargs['result']
			if not isinstance(result, str):
				try:
					kwargs['result'] = json.dumps(result)
				except (TypeError, ValueError) as e:
					# Fallback: store error info for non-serializable objects
					kwargs['result'] = json.dumps({
						'_type': type(result).__name__,
						'_value': str(result),
						'_serialization_error': str(e)
					})

		# Build SET clause dynamically
		set_parts = []
		values = []

		for key, value in kwargs.items():
			if key in ('status', 'result', 'error', 'traceback', 'started_at', 'completed_at', 'worker_id', 'priority', 'timeout'):
				set_parts.append(f"{key} = ?")
				values.append(value)

		if not set_parts:
			return

		values.append(task_id)
		query = f"UPDATE tasks SET {', '.join(set_parts)} WHERE id = ?"

		with self.db() as db:
			db.execute(query, tuple(values))

	def get(self, task_id: int) -> dict | None:
		"""
		Retrieve task by ID.

		Args:
			task_id: Task ID

		Returns:
			Task record as dict or None if not found
		"""
		with self.db() as db:
			cursor = db.execute("""
				SELECT id, name, status, priority, timeout, params, result,
					   error, traceback, created_at, started_at, completed_at, worker_id,
					   is_async, module, qualname
				FROM tasks
				WHERE id = ?
			""", (task_id,))

			row = cursor.fetchone()
			if not row:
				return None

			return {
				'id': row[0],
				'name': row[1],
				'status': row[2],
				'priority': row[3],
				'timeout': row[4],
				'params': row[5],
				'result': row[6],
				'error': row[7],
				'traceback': row[8],
				'created_at': row[9],
				'started_at': row[10],
				'completed_at': row[11],
				'worker_id': row[12],
				'is_async': bool(row[13]) if row[13] is not None else False,
				'module': row[14],
				'qualname': row[15]
			}

	def get_by_status(self, status: str) -> list[dict]:
		"""
		Get all tasks with given status.

		Args:
			status: Task status to filter by

		Returns:
			List of task records
		"""
		with self.db() as db:
			cursor = db.execute("""
				SELECT id, name, status, priority, timeout, params, result,
					   error, traceback, created_at, started_at, completed_at, worker_id
				FROM tasks
				WHERE status = ?
				ORDER BY priority DESC, created_at ASC
			""", (status,))

			rows = cursor.fetchall()
			return [
				{
					'id': row[0],
					'name': row[1],
					'status': row[2],
					'priority': row[3],
					'timeout': row[4],
					'params': row[5],
					'result': row[6],
					'error': row[7],
					'traceback': row[8],
					'created_at': row[9],
					'started_at': row[10],
					'completed_at': row[11],
					'worker_id': row[12]
				}
				for row in rows
			]

	def delete(self, task_id: int) -> bool:
		"""
		Delete task record.

		Args:
			task_id: Task ID to delete

		Returns:
			bool: True if deletion was successful, False otherwise
		"""
		with self.db() as db:
			db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
			return db.rowcount > 0

	def cleanup(self, older_than_days: int = 7) -> int:
		"""
		Delete old completed/failed/timeout tasks.

		Args:
			older_than_days: Delete tasks older than this many days

		Returns:
			Number of tasks deleted
		"""
		cutoff = time.time() - (older_than_days * 24 * 60 * 60)

		with self.db() as db:
			cursor = db.execute("""
				DELETE FROM tasks
				WHERE status IN (?, ?, ?)
				AND completed_at < ?
			""", (Task.TaskStatus.COMPLETED, Task.TaskStatus.FAILED, Task.TaskStatus.TIMEOUT, cutoff))

			return cursor.rowcount

	def get_all(self, limit: int = 50, offset: int = 0) -> list[dict]:
		"""Get all tasks with pagination"""
		with self.db() as db:
			cursor = db.execute("""
				SELECT id, name, status, priority, timeout, params, result,
					   error, traceback, created_at, started_at, completed_at, worker_id
				FROM tasks
				ORDER BY created_at DESC
				LIMIT ? OFFSET ?
			""", (limit, offset))

			rows = cursor.fetchall()
			return [
				{
					'id': row[0],
					'name': row[1],
					'status': row[2],
					'priority': row[3],
					'timeout': row[4],
					'params': row[5],
					'result': row[6],
					'error': row[7],
					'traceback': row[8],
					'created_at': row[9],
					'started_at': row[10],
					'completed_at': row[11],
					'worker_id': row[12]
				}
				for row in rows
			]

	def get_count(self) -> int:
		"""Get total count of tasks"""
		with self.db() as db:
			cursor = db.execute("SELECT COUNT(*) FROM tasks")
			result = cursor.fetchone()
			return result[0] if result else 0

	def get_column_definitions(self) -> list[dict]:
		"""Get column definitions for admin UI"""
		return [
			{"key": "id", "label": "ID", "type": "number", "sortable": True, "truncate": False},
			{"key": "name", "label": "Name", "type": "text", "sortable": True, "truncate": True},
			{"key": "status", "label": "Status", "type": "status", "sortable": True, "truncate": False},
			{"key": "priority", "label": "Priority", "type": "number", "sortable": True, "truncate": False},
			{"key": "timeout", "label": "Timeout", "type": "number", "sortable": True, "truncate": False},
			{"key": "created_at", "label": "Created", "type": "date", "sortable": True, "truncate": False},
			{"key": "started_at", "label": "Started", "type": "date", "sortable": True, "truncate": False},
			{"key": "completed_at", "label": "Completed", "type": "date", "sortable": True, "truncate": False},
			{"key": "worker_id", "label": "Worker", "type": "text", "sortable": True, "truncate": True},
		]


def setup(manager: 'Manager[ABCPlugin]', /):
	"""Setup function for model registration"""
	return Task(manager)
