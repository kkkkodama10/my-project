# domain/repositories.py

from abc import ABC, abstractmethod
from typing import List
from .entities import Task

class TaskRepository(ABC):
    """Abstract base class for task repository."""
    @abstractmethod
    def add(self, task: Task) -> None:
        """Add a task to the repository."""
        pass
    @abstractmethod
    def get(self, task_id: str) -> Task:
        """Get a task by its ID."""
        pass
    @abstractmethod
    def update(self, task: Task) -> None:
        """Update a task in the repository."""
        pass
    @abstractmethod
    def delete(self, task_id: str) -> None:
        """Delete a task from the repository."""
        pass
    @abstractmethod
    def list_all(self) -> List[Task]:
        """List all tasks in the repository."""
        pass