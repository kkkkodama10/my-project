# infrastructure/repository_impl.py

from typing import Dict, List
from domain.entities import Task
from domain.repositories import TaskRepository

class InMemoryTaskRepository(TaskRepository):
    """In-memory implementation of TaskRepository."""
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        
    def add(self, task: Task) -> None:
        """Add a new task."""
        self._tasks[task.id] = task
    def get(self, task_id: str) -> Task:
        """Get a task by its ID."""
        if task_id not in self._tasks:
            raise KeyError(f"Task with ID {task_id} not found.")
        return self._tasks[task_id]
    def update(self, task: Task) -> None:
        """Update an existing task."""
        if task.id not in self._tasks:
            raise KeyError(f"Task with ID {task.id} not found.")
        self._tasks[task.id] = task
    def delete(self, task_id: str) -> None:
        """Delete a task."""
        if task_id not in self._tasks:
            raise KeyError(f"Task with ID {task_id} not found.")
        del self._tasks[task_id]
    def list_all(self) -> List[Task]:
        """List all tasks."""
        return list(self._tasks.values())