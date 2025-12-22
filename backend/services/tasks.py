"""
Task service for background task management.

Provides task registration, submission, and status tracking.
Tasks are executed by separate worker processes (see backend.worker).
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Any, Optional
import threading
import inspect
import time
import subprocess
import sys

if TYPE_CHECKING:
    from _injected import manager, require, validate_setup
    from .logs import Service as Logs

from ..manager import Manager
from .settings import Service as Settings
from ..plugins.model import Plugin as Models
from ._base_service import ABCService


class Service(ABCService):
    """
    Task service for background task management.

    Responsibilities:
    - Register task functions with metadata (module, qualname, async status)
    - Submit tasks to database queue
    - Query task status
    - Provide worker process statistics
    """

    def __init__(self, manager: Manager[ABCService]):
        self.manager = manager
        self._settings: Optional[Settings] = None
        self._logs: Optional[Logs] = None
        self._task_model = None

        # Task registry: {name: {module, qualname, is_async, timeout}}
        self._registry: dict[str, dict[str, Any]] = {}
        self._registry_lock = threading.Lock()

        self._ready = True

    @property
    def settings(self) -> Settings:
        """Lazy-load settings service."""
        if self._settings is None or not self._settings.ready:
            self._settings = self.manager.get[Settings]('settings')
        return self._settings

    @property
    def logs(self) -> Logs:
        """Lazy-load logs service."""
        if self._logs is None or not self._logs.ready:
            from .logs import Service as Logs
            self._logs = self.manager.get[Logs]('logs')
        return self._logs

    @property
    def task_model(self):
        """Lazy-load task model."""
        if self._task_model is None:
            from ..plugins import manager as plugin_manager
            self._task_model = plugin_manager.get[Models]('models').tasks
        return self._task_model

    @property
    def name(self) -> str:
        return "tasks"

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def registry(self) -> dict[str, dict[str, Any]]:
        """Get copy of task registry."""
        with self._registry_lock:
            return dict(self._registry)

    @property
    def workers_enabled(self) -> bool:
        """
        Check if workers are enabled (compatibility property).

        In the new architecture, this checks if a worker process is running.
        """
        return self.is_worker_running()

    @property
    def _worker_count(self) -> int:
        """
        Get worker count setting (compatibility property).

        In the new architecture, this is informational only.
        The worker manager can spawn this many concurrent subprocesses.
        """
        return self.settings.task_worker_count

    @property
    def is_paused(self) -> bool:
        """
        Check if task system is paused (compatibility property).

        In the new architecture, there is no pause mechanism.
        Always returns False.
        """
        return False

    def register(self, func: Callable | None = None, *, name: str | None = None, timeout: float | None = None) -> Callable:
        """
        Decorator to register task functions.

        Stores metadata for worker processes to dynamically load and execute tasks.

        Args:
            func: Task function to register
            name: Optional custom name (defaults to function name)
            timeout: Default timeout in seconds (None = no timeout)

        Returns:
            The original function unchanged

        Usage:
            @tasks.register
            def send_email(to: str, subject: str, body: str):
                ...

            @tasks.register(name="custom_name", timeout=300.0)
            def process_data(data_id: int):
                ...

            @tasks.register
            async def async_task(param: str):
                ...
        """
        def decorator(f: Callable) -> Callable:
            task_name = name if name is not None else f.__name__

            with self._registry_lock:
                self._registry[task_name] = {
                    # Metadata for worker process to load task
                    'module': f.__module__,
                    'qualname': f.__qualname__,
                    'is_async': inspect.iscoroutinefunction(f),
                    'timeout': timeout,

                    # Keep function reference for inspection
                    'func': f
                }

            self.logs.debug(
                f"Registered task",
                service="tasks",
                task_name=task_name,
                module=f.__module__,
                qualname=f.__qualname__,
                is_async=inspect.iscoroutinefunction(f),
                timeout=timeout
            )

            return f

        # Support both @register and @register()
        if func is not None:
            return decorator(func)
        return decorator

    def submit(self, task_name: str, params: dict | None = None, priority: int = 0, timeout: float | None = None) -> int:
        """
        Submit a task to the queue.

        Creates a task record in the database. Worker processes poll the database
        and execute pending tasks in separate subprocesses.

        Args:
            task_name: Name of registered task function
            params: Dictionary of parameters to pass to task function
            priority: Task priority (higher = more important, default 0)
            timeout: Timeout in seconds (overrides registered default, None = no timeout)

        Returns:
            task_id: Database ID of created task

        Raises:
            KeyError: If task_name not registered
        """
        with self._registry_lock:
            if task_name not in self._registry:
                raise KeyError(f"Task '{task_name}' is not registered")

            task_info = self._registry[task_name]

            # Get default timeout from registry if not specified
            if timeout is None:
                timeout = task_info['timeout']

        # Create task record in database (this is the queue)
        task_id = self.task_model.create(
            name=task_name,
            params=params,
            priority=priority,
            timeout=timeout,
            module=task_info['module'],
            qualname=task_info['qualname'],
            is_async=task_info['is_async']
        )

        self.logs.info(
            f"Task submitted",
            service="tasks",
            task_id=task_id,
            task_name=task_name,
            priority=priority
        )

        return task_id

    def get_status(self, task_id: int) -> dict | None:
        """
        Get current status of a task.

        Args:
            task_id: Task ID

        Returns:
            Task record dict or None if not found
        """
        return self.task_model.get(task_id)

    def get_pending_count(self) -> int:
        """
        Get count of pending tasks.

        Returns:
            Number of tasks with status='pending'
        """
        from ..plugins.models.tasks import Task

        pending_tasks = self.task_model.get_by_status(Task.TaskStatus.PENDING)
        return len(pending_tasks)

    def get_running_count(self) -> int:
        """
        Get count of running tasks.

        Returns:
            Number of tasks with status='running'
        """
        from ..plugins.models.tasks import Task

        running_tasks = self.task_model.get_by_status(Task.TaskStatus.RUNNING)
        return len(running_tasks)

    def get_running_tasks(self) -> list[dict]:
        """
        Get list of running tasks.

        Returns:
            List of running task records
        """
        from ..plugins.models.tasks import Task

        return self.task_model.get_by_status(Task.TaskStatus.RUNNING)

    def get_pending_tasks(self) -> list[dict]:
        """
        Get list of pending tasks.

        Returns:
            List of pending task records
        """
        from ..plugins.models.tasks import Task

        return self.task_model.get_by_status(Task.TaskStatus.PENDING)

    def get_stats(self) -> dict[str, Any]:
        """
        Get task system statistics.

        Returns:
            Dictionary with task counts and worker status
        """
        from ..plugins.models.tasks import Task

        return {
            'pending': self.get_pending_count(),
            'running': self.get_running_count(),
            'registered_tasks': len(self._registry),
            'worker_running': self.is_worker_running()
        }

    def is_worker_running(self) -> bool:
        """
        Check if a worker process is running.

        Returns:
            True if worker process is detected, False otherwise
        """
        try:
            # Try to find worker process by command line
            result = subprocess.run(
                ['pgrep', '-f', 'python.*backend.worker'],
                capture_output=True,
                text=True,
                timeout=1
            )
            return result.returncode == 0 and bool(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def list_tasks(self, status: str | None = None, limit: int = 100) -> list[dict]:
        """
        List tasks, optionally filtered by status.

        Args:
            status: Filter by status (pending, running, completed, failed, timeout)
            limit: Maximum number of tasks to return

        Returns:
            List of task records
        """
        if status:
            tasks = self.task_model.get_by_status(status)
        else:
            # Get all recent tasks
            tasks = self.task_model.get_recent(limit)

        return tasks[:limit]

    def cancel_task(self, task_id: int) -> bool:
        """
        Cancel a pending task.

        Note: Only pending tasks can be cancelled. Running tasks cannot be stopped.

        Args:
            task_id: Task ID to cancel

        Returns:
            True if cancelled, False if not found or not pending
        """
        task = self.task_model.get(task_id)
        if not task:
            return False

        from ..plugins.models.tasks import Task

        if task['status'] != Task.TaskStatus.PENDING:
            self.logs.warning(
                f"Cannot cancel task - not pending",
                service="tasks",
                task_id=task_id,
                status=task['status']
            )
            return False

        # Update to cancelled status (treated as failed)
        self.task_model.update(
            task_id,
            status=Task.TaskStatus.FAILED,
            error='Task cancelled by user',
            completed_at=time.time()
        )

        self.logs.info(
            f"Task cancelled",
            service="tasks",
            task_id=task_id
        )

        return True

    def cleanup_old_tasks(self, days: int | None = None) -> int:
        """
        Clean up old completed/failed tasks.

        Args:
            days: Delete tasks older than this many days (default: from settings)

        Returns:
            Number of tasks deleted
        """
        if days is None:
            days = self.settings.task_cleanup_days

        cutoff_time = time.time() - (days * 24 * 60 * 60)

        deleted = self.task_model.delete_old(cutoff_time)

        self.logs.info(
            f"Cleaned up old tasks",
            service="tasks",
            deleted=deleted,
            days=days
        )

        return deleted


def setup(manager: Manager[ABCService], /):
    """Initialize task service."""
    require('settings')
    require('logs')
    return Service(manager)


if TYPE_CHECKING:
    setup = validate_setup(setup)
