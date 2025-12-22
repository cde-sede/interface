#!/usr/bin/env python3
"""
Task Worker Process

Polls database for pending tasks and executes them in separate subprocesses.
Provides true parallelism by bypassing Python's GIL.

Two execution modes:
1. Manager mode (default): Polls DB and spawns subprocesses for tasks
   Usage: python -m backend.worker

2. Execute mode: Runs a specific task (called by manager)
   Usage: python -m backend.worker --execute-task <task_id>
"""

import os
import sys
import time
import signal
import argparse
import importlib
import asyncio
import inspect
import traceback
import subprocess
import json
from typing import Optional, Any, Dict


class WorkerContext:
    """
    Worker context with lazy-loaded services and models.
    Provides type-safe access to backend services.
    """

    def __init__(self):
        # Import managers
        from backend.services import manager as service_manager
        from backend.plugins import manager as plugin_manager

        self.service_manager = service_manager
        self.plugin_manager = plugin_manager

        # Cached instances
        self._logs = None
        self._settings = None
        self._socketio = None
        self._db = None
        self._tasks_model = None

    @property
    def logs(self):
        """Lazy-load logs service."""
        if self._logs is None or not self._logs.ready:
            from backend.services.logs import Service as Logs
            self._logs = self.service_manager.get[Logs]('logs')
        return self._logs

    @property
    def settings(self):
        """Lazy-load settings service."""
        if self._settings is None or not self._settings.ready:
            from backend.services.settings import Service as Settings
            self._settings = self.service_manager.get[Settings]('settings')
        return self._settings

    @property
    def socketio(self):
        """Lazy-load socketio service."""
        if self._socketio is None or not self._socketio.ready:
            from backend.services.socketio import Service as SocketIO
            self._socketio = self.service_manager.get[SocketIO]('socketio')
        return self._socketio

    @property
    def db(self):
        """Lazy-load db service."""
        if self._db is None or not self._db.ready:
            from backend.services.db import Service as DB
            self._db = self.service_manager.get[DB]('db')
        return self._db

    @property
    def tasks_model(self):
        """Lazy-load tasks model."""
        if self._tasks_model is None:
            from backend.plugins.model import Plugin as Models
            models = self.plugin_manager.get[Models]('models')
            self._tasks_model = models.tasks
        return self._tasks_model


def initialize_worker():
    """Initialize services, plugins, and return worker context."""
    from backend.services import manager as service_manager
    from backend.plugins import manager as plugin_manager

    # Load all services
    for service in service_manager.list_plugins():
        service_manager.load(service)

    # Load all plugins (for models and task registrations)
    for plugin in plugin_manager.list_plugins():
        plugin_manager.load(plugin)

    # Return context with lazy-loaded services
    return WorkerContext()


def load_task_function(module_path: str, qualname: str):
    """
    Dynamically import and return task function.

    Args:
        module_path: Module path (e.g., 'backend.plugins.downloader' or just 'downloader')
        qualname: Qualified name (e.g., 'download_task' or 'Downloader.download_task')

    Returns:
        Callable task function
    """
    # Handle shortened module names from the plugin manager
    # The manager might store just 'downloader' instead of 'backend.plugins.downloader'
    if '.' not in module_path:
        # Try common prefixes
        for prefix in ['backend.plugins', 'backend.services', 'backend']:
            try:
                full_path = f'{prefix}.{module_path}'
                module = importlib.import_module(full_path)
                break
            except (ImportError, ModuleNotFoundError):
                continue
        else:
            # Last resort: try as-is
            module = importlib.import_module(module_path)
    else:
        module = importlib.import_module(module_path)

    # Navigate nested qualnames (e.g., 'ClassName.method_name')
    func = module
    for attr in qualname.split('.'):
        func = getattr(func, attr)

    return func


def execute_task_in_subprocess(task_id: int, ctx: WorkerContext) -> None:
    """
    Execute a task in a separate subprocess.

    Args:
        task_id: Database task ID
        ctx: Worker context with services
    """
    # Fetch task from database to get timeout
    task = ctx.tasks_model.get(task_id)
    if not task:
        ctx.logs.warning(f"Task {task_id} not found", worker="task_worker")
        return

    task_name = task['name']
    timeout = task.get('timeout')

    ctx.logs.info(
        f"Spawning subprocess for task",
        task_id=task_id,
        task_name=task_name,
        timeout=timeout
    )

    # Spawn subprocess to execute the task
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'backend.worker', '--execute-task', str(task_id)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd()
        )

        if result.returncode != 0:
            ctx.logs.error(
                f"Task subprocess failed",
                task_id=task_id,
                task_name=task_name,
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr
            )
        else:
            ctx.logs.info(
                f"Task subprocess completed",
                task_id=task_id,
                task_name=task_name
            )

    except subprocess.TimeoutExpired:
        # Subprocess timed out - update task status
        ctx.logs.warning(
            f"Task subprocess timed out",
            task_id=task_id,
            task_name=task_name,
            timeout=timeout
        )

        ctx.tasks_model.update(
            task_id,
            status='timeout',
            error='Task exceeded timeout',
            completed_at=time.time()
        )

        ctx.socketio.emit('task_update', {
            'task_id': task_id,
            'status': 'timeout',
            'task_name': task_name
        })

    except Exception as e:
        ctx.logs.error(
            f"Failed to spawn task subprocess",
            task_id=task_id,
            task_name=task_name,
            error=str(e),
            traceback=traceback.format_exc()
        )


def execute_task_direct(task_id: int) -> None:
    """
    Execute a task directly in this process (called from subprocess).

    Args:
        task_id: Database task ID
    """
    # Initialize context in subprocess
    ctx = initialize_worker()

    # Fetch task from database
    task = ctx.tasks_model.get(task_id)
    if not task:
        print(f"ERROR: Task {task_id} not found", file=sys.stderr)
        sys.exit(1)

    task_name = task['name']
    module = task.get('module')
    qualname = task.get('qualname')
    is_async = task.get('is_async', False)
    timeout = task.get('timeout')

    # Deserialize params (stored as JSON string in DB)
    params_json = task.get('params')
    if params_json:
        params = json.loads(params_json) if isinstance(params_json, str) else params_json
    else:
        params = {}

    ctx.logs.info(
        f"Executing task in subprocess",
        task_id=task_id,
        task_name=task_name,
        task_module=module,  # Renamed to avoid logging module conflict
        task_qualname=qualname,
        is_async=is_async,
        pid=os.getpid()
    )

    # Update status to RUNNING
    ctx.tasks_model.update(
        task_id,
        status='running',
        started_at=time.time(),
        worker_id=f"Worker-{os.getpid()}"
    )

    ctx.socketio.emit('task_update', {
        'task_id': task_id,
        'status': 'running',
        'task_name': task_name
    })

    try:
        # Load task function
        task_func = load_task_function(module, qualname)

        # Execute based on async status
        if is_async:
            result = asyncio.run(task_func(**params))
        else:
            result = task_func(**params)

        # Success - model will automatically JSON-serialize the result
        ctx.tasks_model.update(
            task_id,
            status='completed',
            result=result,
            completed_at=time.time()
        )

        ctx.socketio.emit('task_update', {
            'task_id': task_id,
            'status': 'completed',
            'task_name': task_name,
            'result': result
        })

        ctx.logs.info(
            f"Task completed successfully",
            task_id=task_id,
            task_name=task_name
        )

        sys.exit(0)

    except Exception as e:
        # Failure
        error_trace = traceback.format_exc()

        ctx.tasks_model.update(
            task_id,
            status='failed',
            error=str(e),
            traceback=error_trace,
            completed_at=time.time()
        )

        ctx.socketio.emit('task_update', {
            'task_id': task_id,
            'status': 'failed',
            'task_name': task_name,
            'error': str(e)
        })

        ctx.logs.error(
            f"Task failed",
            task_id=task_id,
            task_name=task_name,
            error=str(e),
            traceback=error_trace
        )

        sys.exit(1)


def worker_loop(ctx: WorkerContext, worker_id: int):
    """
    Main worker loop - polls database for tasks.

    Args:
        ctx: Worker context with services
        worker_id: Worker process ID
    """
    ctx.logs.info(f"Worker started", worker_id=worker_id, pid=os.getpid())

    # Poll interval from settings (default 0.5s)
    poll_interval = getattr(ctx.settings, 'worker_poll_interval', 0.5)

    while True:
        try:
            # Query database for pending task (highest priority first)
            with ctx.db() as db:
                cursor = db.execute("""
                    SELECT id FROM tasks
                    WHERE status = 'pending'
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                """)

                row = cursor.fetchone()

            if row:
                task_id = row[0]
                execute_task_in_subprocess(task_id, ctx)
            else:
                # No tasks, sleep briefly
                time.sleep(poll_interval)

        except KeyboardInterrupt:
            ctx.logs.info(f"Worker received shutdown signal", worker_id=worker_id)
            break
        except Exception as e:
            ctx.logs.error(
                f"Worker error",
                worker_id=worker_id,
                error=str(e),
                traceback=traceback.format_exc()
            )
            time.sleep(1)  # Back off on error


def main():
    """Main entry point for worker process."""
    parser = argparse.ArgumentParser(description='Task Worker Process')
    parser.add_argument(
        '--execute-task',
        type=int,
        default=None,
        metavar='TASK_ID',
        help='Execute a specific task by ID (subprocess mode)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help='Number of concurrent worker processes (default: from settings)'
    )
    args = parser.parse_args()

    # Execute mode: Run a specific task in this subprocess
    if args.execute_task is not None:
        execute_task_direct(args.execute_task)
        return

    # Manager mode: Poll database and spawn subprocesses
    print("Initializing services and plugins...")
    ctx = initialize_worker()

    # Get settings
    worker_count = args.workers or ctx.settings.task_worker_count

    print(f"Starting worker manager (PID: {os.getpid()})...")
    print(f"Will spawn subprocesses for each task (max concurrent: {worker_count})")

    # For now, single manager process
    # Future: Could run multiple managers for horizontal scaling
    worker_id = 0

    # Setup signal handlers for graceful shutdown
    def shutdown_handler(signum, frame):
        print("\nShutting down worker manager...")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Start worker loop
    worker_loop(ctx, worker_id)


if __name__ == '__main__':
    main()
