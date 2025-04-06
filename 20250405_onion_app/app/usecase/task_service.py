# usecase/task_service.py

from datetime import datetime
from typing import List
from domain.entities import Task
from domain.repositories import TaskRepository

class TaskService:
    """TaskService class to manage tasks."""
    
    def __init__(self, repository: TaskRepository):
        self.repository = repository
        
    def create_task(self, title: str, description: str) -> Task:
        """Create a new task."""
        task = Task(title=title, description=description)
        self.repository.add(task)
        return task
    def get_task(self, task_id: str) -> Task:
        """Get a task by its ID."""
        return self.repository.get(task_id)
    def update_task(self, task_id: str, title: str, description: str, is_completed: bool) -> Task:
        """Update a task."""
        task = self.repository.get(task_id)
        if title:
            task.title = title
        if description:
            task.description = description
        if is_completed is not None:
            task.is_completed = is_completed
        task.updated_at = datetime.utcnow()
        self.repository.update(task)
        return task
    def delete_task(self, task_id: str) -> None:
        """Delete a task."""
        self.repository.delete(task_id)
    def list_tasks(self) -> List[Task]:
        """List all tasks."""
        return self.repository.list_all()