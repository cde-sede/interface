"""
Task service for background task execution.

Manages task registration, submission, and execution via worker thread pool.
"""
from typing import TYPE_CHECKING, Callable, Any
import threading
import time
import json
import traceback
from queue import PriorityQueue, Empty
import os
import fcntl

if TYPE_CHECKING:
    from _injected import manager, require, validate_setup

from ..manager import Manager
from ..services.settings import Service as Settings
from ..plugins.models.tasks import Task
from ..plugins.model import Plugin as Models
from ._base_service import ABCService


class Service(ABCService):
    """
    Task service for background task execution.

    Features:
    - Queue-based execution with configurable worker thread pool
    - Priority-based task scheduling
    - Timeout support with automatic timeout detection
    - Pause/Resume capability
    - Full manager access for tasks
    - WSGI-safe: Uses file locking to ensure only one process runs workers
    """

    def __init__(self, manager: Manager[ABCService]):
        self.manager = manager
        self.settings = manager.get[Settings]('settings')
        self._task_model = None

        # Task registry: {name: {func: Callable, timeout: float | None}}
        self._registry: dict[str, dict[str, Any]] = {}
        self._registry_lock = threading.Lock()

        # Priority queue: items are tuples (-priority, created_at, task_id)
        # Negative priority for max-heap behavior (higher priority first)
        self._queue: PriorityQueue[tuple[int, float, int]] = PriorityQueue()

        # Worker management
        self._workers: list[threading.Thread] = []
        self._worker_count = self.settings.task_worker_count
        self._stop_event = threading.Event()
        self._paused_event = threading.Event()
        self._paused_event.set()  # Not paused initially

        # State tracking
        self._lock = threading.Lock()
        self._running_tasks: dict[int, threading.Thread] = {}  # task_id -> thread

        # WSGI safety: file lock to ensure only one process runs workers
        self._lock_file = None
        self._workers_enabled = False

        self._ready = False

        # Try to start workers if enabled
        if self.settings.task_workers_enabled:
            self._try_acquire_worker_lock()

        self._ready = True

    @property
    def task_model(self):
        """Lazy-load task model (plugins may not be loaded at service init time)"""
        if self._task_model is None:
            self._task_model = self.manager.get[Models]('plugins.models').tasks
        return self._task_model

    @property
    def name(self) -> str:
        return "tasks"

    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def is_paused(self) -> bool:
        """Check if task system is paused"""
        return not self._paused_event.is_set()

    @property
    def workers_enabled(self) -> bool:
        """Check if workers are enabled in this process"""
        return self._workers_enabled

    def _try_acquire_worker_lock(self) -> bool:
        """
        Try to acquire file lock for worker management.
        Only one process should run workers to avoid conflicts in WSGI environments.

        Includes stale lock detection - if the lock holder process is dead,
        the lock is removed and acquisition is retried.

        Returns:
            True if lock acquired and workers started, False otherwise
        """
        lock_path = self.settings.task_worker_lock_file

        try:
            # Create lock file if it doesn't exist
            os.makedirs(os.path.dirname(lock_path), exist_ok=True)
            self._lock_file = open(lock_path, 'w')

            # Try to acquire exclusive lock (non-blocking)
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Lock acquired! Write our PID
            self._lock_file.write(str(os.getpid()))
            self._lock_file.flush()

            # Start workers
            self._start_workers()
            self._workers_enabled = True

            print(f"[Tasks] Worker lock acquired by PID {os.getpid()}, starting {self._worker_count} workers")
            return True

        except (OSError, IOError) as e:
            # Lock already held - check if holder is still alive
            if self._lock_file:
                self._lock_file.close()
                self._lock_file = None

            # Check for stale lock
            if self._check_and_clear_stale_lock(lock_path):
                # Stale lock was cleared, try again (recursive, but only once)
                print(f"[Tasks] Cleared stale lock, retrying acquisition...")
                return self._try_acquire_worker_lock_once(lock_path)

            return False

    def _try_acquire_worker_lock_once(self, lock_path: str) -> bool:
        """
        Try to acquire lock once without stale lock checking (to prevent recursion).

        Args:
            lock_path: Path to lock file

        Returns:
            True if lock acquired, False otherwise
        """
        try:
            self._lock_file = open(lock_path, 'w')
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            self._lock_file.write(str(os.getpid()))
            self._lock_file.flush()

            self._start_workers()
            self._workers_enabled = True

            print(f"[Tasks] Worker lock acquired by PID {os.getpid()} after clearing stale lock")
            return True

        except (OSError, IOError):
            if self._lock_file:
                self._lock_file.close()
                self._lock_file = None
            return False

    def _check_and_clear_stale_lock(self, lock_path: str) -> bool:
        """
        Check if the lock file is held by a dead process and clear it if so.

        Args:
            lock_path: Path to lock file

        Returns:
            True if stale lock was cleared, False otherwise
        """
        try:
            # Try to read the PID from the lock file
            if not os.path.exists(lock_path):
                return False

            with open(lock_path, 'r') as f:
                content = f.read().strip()
                if not content:
                    # Empty lock file, consider it stale
                    os.remove(lock_path)
                    print(f"[Tasks] Removed empty lock file")
                    return True

                try:
                    pid = int(content)
                except ValueError:
                    # Invalid PID, remove lock file
                    os.remove(lock_path)
                    print(f"[Tasks] Removed lock file with invalid PID: {content}")
                    return True

            # Check if process is still running
            try:
                # Send signal 0 to check if process exists (doesn't actually kill it)
                os.kill(pid, 0)
                # Process exists, lock is valid
                print(f"[Tasks] Lock held by running process PID {pid}")
                return False
            except OSError:
                # Process doesn't exist, lock is stale
                os.remove(lock_path)
                print(f"[Tasks] Removed stale lock from dead process PID {pid}")
                return True

        except Exception as e:
            # If anything goes wrong, don't remove the lock file (safe default)
            print(f"[Tasks] Error checking stale lock: {e}")
            return False

    def _release_worker_lock(self) -> None:
        """Release worker lock file"""
        if self._lock_file:
            try:
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
                self._lock_file.close()
            except:
                pass
            finally:
                self._lock_file = None

    def register(self, func: Callable | None = None, *, name: str | None = None, timeout: float | None = None) -> Callable:
        """
        Decorator to register task functions.

        Args:
            func: Task function to register
            name: Optional custom name (defaults to function name)
            timeout: Default timeout in seconds (None = no timeout)

        Usage:
            @tasks.register
            def send_email(to: str, subject: str, body: str):
                ...

            @tasks.register(name="custom_name", timeout=300.0)
            def process_data(data_id: int):
                ...
        """
        def decorator(f: Callable) -> Callable:
            task_name = name if name is not None else f.__name__

            with self._registry_lock:
                self._registry[task_name] = {
                    'func': f,
                    'timeout': timeout
                }

            return f

        # Support both @register and @register()
        if func is not None:
            return decorator(func)
        return decorator

    def submit(self, task_name: str, params: dict | None = None, priority: int = 0, timeout: float | None = None) -> int:
        """
        Submit a task to the queue.

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

            # Get default timeout from registry if not specified
            if timeout is None:
                timeout = self._registry[task_name]['timeout']

        # Create task record in database
        task_id = self.task_model.create(
            name=task_name,
            params=params,
            priority=priority,
            timeout=timeout
        )

        # Add to priority queue
        # Use negative priority for max-heap behavior
        created_at = time.time()
        self._queue.put((-priority, created_at, task_id))

        return task_id

    def get_status(self, task_id: int) -> dict | None:
        """
        Get current status of a task.

        Args:
            task_id: Task ID

        Returns:
            Task record as dict or None if not found
        """
        return self.task_model.get(task_id)

    def cancel(self, task_id: int) -> bool:
        """
        Attempt to cancel a pending task.

        Args:
            task_id: Task ID to cancel

        Returns:
            True if cancelled, False if already running/completed
        """
        task = self.task_model.get(task_id)
        if not task:
            return False

        # Can only cancel pending tasks
        if task['status'] != Task.TaskStatus.PENDING:
            return False

        # Mark as failed with cancellation message
        self.task_model.update(
            task_id,
            status=Task.TaskStatus.FAILED,
            error="Task cancelled by user",
            completed_at=time.time()
        )

        return True

    def pause(self) -> None:
        """
        Pause the task system.
        - Currently running tasks continue to completion
        - No new tasks are picked up from the queue
        - New tasks can still be submitted (they queue up)
        """
        self._paused_event.clear()

    def resume(self) -> None:
        """
        Resume the task system.
        - Workers start picking up tasks from queue again
        """
        self._paused_event.set()

    def get_running_tasks(self) -> list[dict]:
        """Get list of currently running tasks"""
        with self._lock:
            task_ids = list(self._running_tasks.keys())

        return [self.task_model.get(tid) or (_ for _ in ()).throw(Exception('how'))
				 for tid in task_ids if self.task_model.get(tid)]

    def cleanup_old_tasks(self, days: int = 7) -> int:
        """
        Delete completed/failed/timeout tasks older than N days.

        Args:
            days: Delete tasks older than this many days

        Returns:
            Number of tasks deleted
        """
        return self.task_model.cleanup(older_than_days=days)

    def _start_workers(self) -> None:
        """Initialize and start worker threads"""
        for i in range(self._worker_count):
            worker = threading.Thread(
                target=self._worker_loop,
                args=(i,),
                name=f"TaskWorker-{i}",
                daemon=True
            )
            worker.start()
            self._workers.append(worker)

    def _stop_workers(self) -> None:
        """Signal workers to stop and wait for graceful shutdown"""
        # Signal stop
        self._stop_event.set()

        # Resume if paused to allow workers to exit
        self._paused_event.set()

        # Wait for all workers to finish
        for worker in self._workers:
            worker.join(timeout=5.0)

        # Release lock file
        self._release_worker_lock()

    def _worker_loop(self, worker_id: int) -> None:
        """
        Main worker loop - pulls tasks from queue and executes them.

        Args:
            worker_id: Worker thread identifier
        """
        while not self._stop_event.is_set():
            try:
                # Wait for system to be unpaused (blocking)
                self._paused_event.wait(timeout=1.0)

                # If still paused or stopped, continue loop
                if not self._paused_event.is_set() or self._stop_event.is_set():
                    continue

                # Try to get task from priority queue (blocking with timeout)
                # Items are tuples: (-priority, created_at, task_id)
                try:
                    priority_item = self._queue.get(timeout=1.0)
                except Empty:
                    continue  # No tasks, check stop/pause events

                _, _, task_id = priority_item

                # Track running task
                with self._lock:
                    self._running_tasks[task_id] = threading.current_thread()

                try:
                    self._execute_task(task_id)
                finally:
                    # Remove from running tasks
                    with self._lock:
                        self._running_tasks.pop(task_id, None)
                    self._queue.task_done()

            except Exception as e:
                # Log unexpected worker errors but continue
                print(f"Worker {worker_id} error: {e}")
                traceback.print_exc()

    def _execute_task(self, task_id: int) -> None:
        """
        Execute a single task with timeout monitoring.

        Args:
            task_id: Task ID to execute
        """
        # Fetch task details
        task_record = self.task_model.get(task_id)
        if not task_record:
            return

        task_name = task_record['name']

        # Get task function
        with self._registry_lock:
            if task_name not in self._registry:
                self.task_model.update(
                    task_id,
                    status=Task.TaskStatus.FAILED,
                    error=f"Task '{task_name}' is not registered",
                    completed_at=time.time()
                )
                return

            task_info = self._registry[task_name]

        task_func = task_info['func']
        params = json.loads(task_record['params']) if task_record['params'] else {}
        timeout = task_record['timeout']

        # Update status to running
        self.task_model.update(
            task_id,
            status=Task.TaskStatus.RUNNING,
            started_at=time.time(),
            worker_id=threading.current_thread().name
        )

        start_time = time.time()
        result_container = {'result': None, 'error': None, 'timed_out': False}

        # Execute with or without timeout
        if timeout is not None:
            def _run_task():
                try:
                    result_container['result'] = task_func(**params)
                except Exception as e:
                    result_container['error'] = e
                    result_container['traceback'] = traceback.format_exc()

            task_thread = threading.Thread(target=_run_task, daemon=True)
            task_thread.start()
            task_thread.join(timeout=timeout)

            if task_thread.is_alive():
                # Task exceeded timeout (thread still running but we abandon it)
                result_container['timed_out'] = True
                elapsed = time.time() - start_time
                self.task_model.update(
                    task_id,
                    status=Task.TaskStatus.TIMEOUT,
                    error=f"Task exceeded timeout of {timeout}s (ran for {elapsed:.2f}s)",
                    completed_at=time.time()
                )
                return
        else:
            # No timeout, execute directly
            try:
                result_container['result'] = task_func(**params)
            except Exception as e:
                result_container['error'] = e
                result_container['traceback'] = traceback.format_exc()

        # Handle result or error
        if result_container['error']:
            self.task_model.update(
                task_id,
                status=Task.TaskStatus.FAILED,
                error=str(result_container['error']),
                traceback=result_container.get('traceback', ''),
                completed_at=time.time()
            )
        else:
            self.task_model.update(
                task_id,
                status=Task.TaskStatus.COMPLETED,
                result=json.dumps(result_container['result']) if result_container['result'] is not None else None,
                completed_at=time.time()
            )


def setup(manager: Manager[ABCService], /):
    """Setup function for service registration"""
    require('settings')
    # Note: plugins.models is lazy-loaded to avoid circular dependency
    return Service(manager)


if TYPE_CHECKING:
    setup = validate_setup(setup)
