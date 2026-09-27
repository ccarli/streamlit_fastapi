"""In-memory store shared by the FastAPI routes and the Streamlit dashboard.

Both run in the same Python process, so they can share plain Python objects.
"""

import threading
from datetime import datetime, timezone

from pydantic import BaseModel


class Task(BaseModel):
    id: int
    title: str
    done: bool = False
    created_at: datetime


_lock = threading.Lock()
_tasks: dict[int, Task] = {}
_next_id = 1


def add_task(title: str) -> Task:
    global _next_id
    with _lock:
        task = Task(id=_next_id, title=title, created_at=datetime.now(timezone.utc))
        _tasks[task.id] = task
        _next_id += 1
        return task


def list_tasks() -> list[Task]:
    with _lock:
        return list(_tasks.values())


def set_done(task_id: int, done: bool) -> Task | None:
    with _lock:
        task = _tasks.get(task_id)
        if task is not None:
            task.done = done
        return task


for title in ("Write the API", "Mount Streamlit", "Ship it"):
    add_task(title)
