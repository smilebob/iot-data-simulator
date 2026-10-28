"""
In-Memory Ring-Buffer Logging System with Live Streaming and Console Dispatch.

This module provides an in-memory logging handler backed by a thread-safe circular
buffer (`collections.deque`). It supports:
- Real-time broadcast dispatching to WebSocket connections for the live UI console.
- Filtering and extraction by log level (DEBUG, INFO, WARNING, ERROR).
- Standard stream logging to `sys.stdout` for container observability (`docker logs`).
- Automatic hook registration across all primary simulator subsystems (`iot_sim.*`).
"""

import collections
import logging
import sys
import time
from typing import Any, Callable, Dict, List, Optional

class InMemoryLogHandler(logging.Handler):
    """
    Circular in-memory logging handler with optional WebSocket broadcast.

    Stores the most recent log records in a fixed-capacity FIFO ring buffer.
    Whenever a record at or above `logging.INFO` is emitted, an optional callback
    is dispatched to stream the log entry directly to connected frontend clients.

    Attributes:
        capacity: Maximum number of entries preserved in the ring buffer.
        buffer: `collections.deque` maintaining the bounded log record history.
    """

    def __init__(self, capacity: int = 200) -> None:
        """
        Initializes the in-memory logging buffer.

        Args:
            capacity: Maximum number of log records to retain. Defaults to 200.
        """
        super().__init__()
        self.capacity: int = capacity
        self.buffer: collections.deque = collections.deque(maxlen=capacity)
        self._counter: int = 0
        self._broadcast_callback: Optional[Callable[[Dict[str, Any]], None]] = None

    def set_broadcast_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Registers an asynchronous or synchronous callback for live streaming.

        Args:
            callback: Function invoked with a serialized dictionary payload
                representing the new log entry.
        """
        self._broadcast_callback = callback

    def emit(self, record: logging.LogRecord) -> None:
        """
        Formats, records, and optionally broadcasts a log entry.

        Args:
            record: Standard Python `logging.LogRecord` instance.
        """
        try:
            self._counter += 1
            msg = self.format(record)
            entry = {
                "id": self._counter,
                "timestamp": time.strftime("%H:%M:%S", time.localtime(record.created)),
                "created": record.created,
                "level": record.levelname,
                "logger": record.name,
                "message": msg,
            }
            self.buffer.append(entry)

            if self._broadcast_callback and record.levelno >= logging.INFO:
                try:
                    self._broadcast_callback({
                        "type": "log",
                        "data": entry
                    })
                except Exception:
                    pass
        except Exception:
            self.handleError(record)

    def get_logs(self, level: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieves formatted log records with optional level filtering and limits.

        Args:
            level: Optional minimum or exact log level ('INFO', 'WARNING', 'ERROR').
                If omitted or 'ALL', all levels are returned.
            limit: Maximum count of recent records to retrieve. Defaults to 100.

        Returns:
            List[Dict[str, Any]]: Sliced list of recent log entry dictionaries.
        """
        logs = list(self.buffer)
        if level and level.upper() != "ALL":
            logs = [entry for entry in logs if entry["level"] == level.upper()]
        return logs[-limit:]

    def clear(self) -> None:
        """Purges all log entries currently stored in the ring buffer."""
        self.buffer.clear()

# Shared singleton instance for the application runtime
log_handler = InMemoryLogHandler(capacity=200)
log_handler.setFormatter(logging.Formatter("%(message)s"))

# Standard console output (sys.stdout) formatted for container engines and docker logs
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"))

# Register handlers on root and primary subsystem loggers
for log_name in (None, "iot_sim", "iot_sim.mqtt", "iot_sim.engine", "iot_sim.http"):
    l = logging.getLogger(log_name)
    l.addHandler(log_handler)
    l.addHandler(console_handler)
    l.setLevel(logging.INFO)
