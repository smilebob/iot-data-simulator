import collections
import logging
import time
from typing import Any, Callable, Dict, List, Optional

class InMemoryLogHandler(logging.Handler):
    """
    Handler de logging en mémoire avec tampon circulaire (200 entrées).
    Permet la consultation des logs et des erreurs via l'API et l'IHM web.
    """

    def __init__(self, capacity: int = 200):
        super().__init__()
        self.capacity = capacity
        self.buffer = collections.deque(maxlen=capacity)
        self._counter = 0
        self._broadcast_callback: Optional[Callable[[Dict[str, Any]], None]] = None

    def set_broadcast_callback(self, callback: Callable[[Dict[str, Any]], None]):
        self._broadcast_callback = callback

    def emit(self, record: logging.LogRecord):
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
        logs = list(self.buffer)
        if level and level.upper() != "ALL":
            logs = [entry for entry in logs if entry["level"] == level.upper()]
        return logs[-limit:]

    def clear(self):
        self.buffer.clear()

import sys

# Instance globale partagée
log_handler = InMemoryLogHandler(capacity=200)
log_handler.setFormatter(logging.Formatter("%(message)s"))

# Sortie console standard (sys.stdout) pour affichage dans 'docker logs'
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"))

for log_name in (None, "iot_sim", "iot_sim.mqtt", "iot_sim.engine", "iot_sim.http"):
    l = logging.getLogger(log_name)
    l.addHandler(log_handler)
    l.addHandler(console_handler)
    l.setLevel(logging.INFO)
