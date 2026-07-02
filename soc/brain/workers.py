from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import threading
import time


@dataclass
class WorkerStatus:
    name: str
    running: bool = False
    last_run: Optional[float] = None
    last_message: Optional[str] = None


class WorkerManager:
    """Simple background worker manager for long-running tasks.

    This is an in-process, synchronous manager intended for local
    development and prototypes. Production deployments should replace
    this with a proper task queue (e.g., Celery/RQ) and process
    supervision.
    """

    def __init__(self):
        self.workers: Dict[str, WorkerStatus] = {}

    def register(self, name: str):
        self.workers[name] = WorkerStatus(name=name)

    def start(self, name: str, target, *args, **kwargs):
        if name not in self.workers:
            self.register(name)

        def _wrap():
            st = self.workers[name]
            st.running = True
            st.last_run = time.time()
            try:
                target(*args, **kwargs)
                st.last_message = 'completed'
            except Exception as e:
                st.last_message = f'error: {e}'
            finally:
                st.running = False

        t = threading.Thread(target=_wrap, daemon=True)
        t.start()
        return t

    def status(self) -> List[Dict]:
        return [dict(name=s.name, running=s.running, last_run=s.last_run, last_message=s.last_message) for s in self.workers.values()]
