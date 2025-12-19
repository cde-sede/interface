from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, cast, Dict, List
if TYPE_CHECKING:
	from _injected import manager, require, validate_setup
	from .socketio import Service as SocketIO, NullSocketIO

from ._base_service import ABCService
from ._manager import Manager
from .settings import Service as Settings
import logging
import logging.handlers
import json
import sys
import os
import re
import threading
import time
from datetime import datetime
from enum import Enum
from pathlib import Path


class LogLevel(Enum):
	DEBUG = logging.DEBUG
	INFO = logging.INFO
	WARNING = logging.WARNING
	ERROR = logging.ERROR
	CRITICAL = logging.CRITICAL


class PrettyFormatter(logging.Formatter):
	"""Pretty formatter with colors and structured output"""

	# ANSI color codes
	COLORS = {
		'DEBUG': '\033[36m',      # Cyan
		'INFO': '\033[32m',       # Green
		'WARNING': '\033[33m',    # Yellow
		'ERROR': '\033[31m',      # Red
		'CRITICAL': '\033[35m',   # Magenta
		'RESET': '\033[0m',       # Reset
		'BOLD': '\033[1m',        # Bold
		'DIM': '\033[2m',         # Dim
	}

	def __init__(self, use_colors: bool = True, format_style: str = "pretty"):
		super().__init__()
		self.use_colors = use_colors
		self.format_style = format_style

	def format(self, record: logging.LogRecord) -> str:
		"""Format log record with pretty colors and structure"""

		# Get timestamp
		timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

		# Get level name and color
		level_name = record.levelname

		# Get service/module name
		service = getattr(record, 'service', record.name)

		# Base message
		message = record.getMessage()

		# Handle structured data
		extra_data = {}
		for key, value in record.__dict__.items():
			if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
			               'levelname', 'levelno', 'lineno', 'module', 'msecs',
			               'message', 'pathname', 'process', 'processName', 'relativeCreated',
			               'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
			               'service']:
				# Only include non-None values
				if value is not None:
					extra_data[key] = value

		# Format based on style
		if self.format_style == "json":
			return self._format_json(timestamp, level_name, service, message, extra_data, record)
		elif self.format_style == "simple":
			return self._format_simple(timestamp, level_name, service, message, record)
		else:  # pretty
			return self._format_pretty(timestamp, level_name, service, message, extra_data, record)

	def _format_json(self, timestamp: str, level_name: str, service: str,
	                 message: str, extra_data: dict, record: logging.LogRecord) -> str:
		"""Format as JSON"""
		log_data = {
			'timestamp': timestamp,
			'level': level_name,
			'service': service,
			'message': message
		}

		if extra_data:
			log_data['data'] = extra_data

		if record.exc_info:
			log_data['exception'] = self.formatException(record.exc_info)

		return json.dumps(log_data)

	def _format_simple(self, timestamp: str, level_name: str, service: str,
	                   message: str, record: logging.LogRecord) -> str:
		"""Format as simple text"""
		parts = [timestamp, level_name, f"[{service}]", message]

		if record.exc_info:
			exc_text = self.formatException(record.exc_info)
			parts.append(f"\n{exc_text}")

		return " ".join(parts)

	def _format_pretty(self, timestamp: str, level_name: str, service: str,
	                   message: str, extra_data: dict, record: logging.LogRecord) -> str:
		"""Format with pretty colors and structure"""
		if self.use_colors:
			level_color = self.COLORS.get(level_name, '')
			reset = self.COLORS['RESET']
			bold = self.COLORS['BOLD']
			dim = self.COLORS['DIM']
		else:
			level_color = reset = bold = dim = ''

		# Format level with fixed width
		level_str = f"{level_color}{level_name:8s}{reset}"
		service_str = f"{dim}[{service}]{reset}"

		# Build the log line
		parts = [f"{dim}{timestamp}{reset}", level_str, service_str, message]

		# Add structured data inline if present and non-empty
		if extra_data:
			# Format as key=value pairs
			data_parts = []
			for key, value in extra_data.items():
				# Format value appropriately
				if isinstance(value, str):
					formatted_value = f'"{value}"' if ' ' in value else value
				else:
					formatted_value = str(value)
				data_parts.append(f"{key}={formatted_value}")

			if data_parts:
				parts.append(f"{dim}({', '.join(data_parts)}){reset}")

		# Add exception info if present (on new lines for readability)
		if record.exc_info:
			exc_text = self.formatException(record.exc_info)
			parts.append(f"\n{level_color}{exc_text}{reset}")

		return " ".join(parts)


class Service(ABCService):
	"""Logging service with pretty printing capabilities"""

	def __init__(self, manager: Manager[ABCService]):
		self.manager = manager
		self._settings: Optional[Settings] = None
		self._socketio: Optional[SocketIO] = None
		self._ready = True
		self._loggers: Dict[str, logging.Logger] = {}

		# Runtime log file for admin page (always enabled)
		self.runtime_log_file = "logs/runtime.log"
		self._runtime_log_handler: Optional[logging.handlers.RotatingFileHandler] = None

		# Track if we should broadcast updates
		self._last_broadcast_time = 0
		self._broadcast_cooldown = 2.0  # Broadcast at most every 2 seconds

		# Configure root logger
		self._configure_root_logger()

	def _configure_root_logger(self):
		"""Configure the root logger with pretty formatter"""
		root_logger = logging.getLogger()

		# Remove existing handlers
		for handler in root_logger.handlers[:]:
			root_logger.removeHandler(handler)

		# Get settings
		log_level_str = self.settings.log_level
		log_colors = self.settings.log_colors
		log_format = self.settings.log_format
		log_output = self.settings.log_output
		log_file_path = self.settings.log_file_path
		log_file_max_bytes = self.settings.log_file_max_bytes
		log_file_backup_count = self.settings.log_file_backup_count

		# Map string level to logging constant
		log_level_map = {
			'DEBUG': logging.DEBUG,
			'INFO': logging.INFO,
			'WARNING': logging.WARNING,
			'ERROR': logging.ERROR,
			'CRITICAL': logging.CRITICAL
		}
		log_level = log_level_map.get(log_level_str, logging.INFO)

		# Set root logger level
		root_logger.setLevel(log_level)

		# Always add runtime log file handler for admin logs page
		try:
			# Create log directory if it doesn't exist
			runtime_log_dir = os.path.dirname(self.runtime_log_file)
			if runtime_log_dir and not os.path.exists(runtime_log_dir):
				os.makedirs(runtime_log_dir, exist_ok=True)

			# Create rotating file handler for runtime logs
			self._runtime_log_handler = logging.handlers.RotatingFileHandler(
				self.runtime_log_file,
				maxBytes=10485760,  # 10MB
				backupCount=3,
				encoding='utf-8'
			)

			# Use simple format for easier parsing
			self._runtime_log_handler.setFormatter(PrettyFormatter(
				use_colors=False,
				format_style="simple"
			))
			self._runtime_log_handler.setLevel(log_level)
			root_logger.addHandler(self._runtime_log_handler)
		except Exception:
			# If runtime log handler fails, continue without it
			pass

		# Add stdout handler if needed
		if log_output in ("stdout", "both"):
			# Determine if colors should be used for console
			# Use colors if: setting is enabled AND stdout is a TTY
			use_colors = log_colors and sys.stdout.isatty()

			console_handler = logging.StreamHandler(sys.stdout)
			console_handler.setFormatter(PrettyFormatter(
				use_colors=use_colors,
				format_style=log_format
			))
			console_handler.setLevel(log_level)
			root_logger.addHandler(console_handler)

		# Add file handler if needed
		if log_output in ("file", "both"):
			try:
				# Create log directory if it doesn't exist
				log_dir = os.path.dirname(log_file_path)
				if log_dir and not os.path.exists(log_dir):
					os.makedirs(log_dir, exist_ok=True)

				# Create rotating file handler
				file_handler = logging.handlers.RotatingFileHandler(
					log_file_path,
					maxBytes=log_file_max_bytes,
					backupCount=log_file_backup_count,
					encoding='utf-8'
				)

				# Files never use colors, even if colors are enabled
				file_handler.setFormatter(PrettyFormatter(
					use_colors=False,
					format_style=log_format
				))
				file_handler.setLevel(log_level)
				root_logger.addHandler(file_handler)

			except (OSError, PermissionError) as e:
				# If file handler fails, log to stderr as fallback
				fallback_handler = logging.StreamHandler(sys.stderr)
				fallback_handler.setFormatter(PrettyFormatter(
					use_colors=False,
					format_style="simple"
				))
				root_logger.addHandler(fallback_handler)
				root_logger.error(f"Failed to create log file handler: {e}",
				                 extra={'service': 'logs'})

	@property
	def settings(self) -> Settings:
		if self._settings is None or not self._settings.ready:
			self._settings = self.manager.get[Settings]('settings')
		return self._settings

	@property
	def socketio(self):
		if self._socketio is None:
			try:
				from .socketio import Service as SocketIO
				self._socketio = self.manager.get[SocketIO]('socketio')
			except:
				# SocketIO not available, return null implementation
				from .socketio import NullSocketIO
				self._socketio = NullSocketIO()
		return self._socketio

	@property
	def name(self) -> str:
		return "logs"

	@property
	def ready(self) -> bool:
		return self._ready

	def get_logger(self, service_name: str) -> logging.Logger:
		"""Get or create a logger for a specific service"""
		if service_name not in self._loggers:
			logger = logging.getLogger(service_name)
			self._loggers[service_name] = logger
		return self._loggers[service_name]

	def log(self, level: LogLevel, message: str, service: str = "app", **kwargs):
		"""Log a message with optional structured data"""
		logger = self.get_logger(service)
		extra = {'service': service}
		extra.update(kwargs)
		logger.log(level.value, message, extra=extra)

		# Broadcast log update to connected clients (with cooldown)
		self._maybe_broadcast_update(level)

	def debug(self, message: str, service: str = "app", **kwargs):
		"""Log a debug message"""
		self.log(LogLevel.DEBUG, message, service, **kwargs)

	def info(self, message: str, service: str = "app", **kwargs):
		"""Log an info message"""
		self.log(LogLevel.INFO, message, service, **kwargs)

	def warning(self, message: str, service: str = "app", **kwargs):
		"""Log a warning message"""
		self.log(LogLevel.WARNING, message, service, **kwargs)

	def error(self, message: str, service: str = "app", **kwargs):
		"""Log an error message"""
		self.log(LogLevel.ERROR, message, service, **kwargs)

	def critical(self, message: str, service: str = "app", **kwargs):
		"""Log a critical message"""
		self.log(LogLevel.CRITICAL, message, service, **kwargs)

	def exception(self, message: str, service: str = "app", exc_info: Any = True, **kwargs):
		"""Log an exception with traceback"""
		logger = self.get_logger(service)
		extra = {'service': service}
		extra.update(kwargs)
		logger.exception(message, exc_info=exc_info, extra=extra)

	def get_recent_logs(self, limit: int = 100, level: Optional[str] = None) -> List[Dict[str, Any]]:
		"""Read recent logs from the runtime log file"""
		logs = []

		try:
			if not os.path.exists(self.runtime_log_file):
				return logs

			# Read the log file
			with open(self.runtime_log_file, 'r', encoding='utf-8') as f:
				lines = f.readlines()

			# Parse log lines (format: "timestamp LEVEL [service] message")
			# Pattern: timestamp level [service] message
			log_pattern = re.compile(r'^(\S+\s+\S+)\s+(\w+)\s+\[([^\]]+)\]\s+(.+)$')

			for line in lines:
				line = line.strip()
				if not line:
					continue

				match = log_pattern.match(line)
				if match:
					timestamp_str, log_level, logger_name, message = match.groups()

					# Filter by level if specified
					if level:
						level_num = getattr(logging, level.upper(), logging.INFO)
						log_level_num = getattr(logging, log_level.upper(), logging.INFO)
						if log_level_num < level_num:
							continue

					logs.append({
						'timestamp': timestamp_str,
						'level': log_level,
						'logger': logger_name,
						'message': message
					})

			# Return most recent logs first
			logs.reverse()

			# Apply limit
			if limit:
				logs = logs[:limit]

			return logs

		except Exception as e:
			# Return error log if reading fails
			return [{
				'timestamp': datetime.now().isoformat(),
				'level': 'ERROR',
				'logger': 'logs',
				'message': f'Failed to read log file: {str(e)}'
			}]

	def clear_logs(self):
		"""Clear the runtime log file"""
		try:
			if os.path.exists(self.runtime_log_file):
				# Truncate the file
				with open(self.runtime_log_file, 'w', encoding='utf-8') as f:
					f.truncate(0)
		except Exception:
			pass

	def _maybe_broadcast_update(self, level: LogLevel):
		"""Broadcast log update via Socket.IO with cooldown to avoid spam"""
		current_time = time.time()

		# Only broadcast if:
		# 1. Enough time has passed since last broadcast (cooldown)
		# 2. OR it's an ERROR/CRITICAL level (always broadcast important logs)
		should_broadcast = (
			(current_time - self._last_broadcast_time) >= self._broadcast_cooldown or
			level.value >= logging.ERROR
		)

		if should_broadcast:
			self._last_broadcast_time = current_time
			try:
				# Broadcast only to users on the logs page
				self.socketio.broadcast_to_page('logs', 'refresh_page', {'page': 'logs'})
			except Exception:
				# SocketIO not available or failed, ignore
				pass


def setup(manager: Manager[ABCService], /):
	require("settings")
	# SocketIO is optional - service will work without it
	return Service(manager)

if TYPE_CHECKING:
	setup = validate_setup(setup)
