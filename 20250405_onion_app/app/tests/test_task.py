# tests/test_task.py

import pytest
from fastapi.testclient import TestClient
from infrastructure.repository_impl import InMemoryTaskRepository
from usecase.task_service import TaskService
from presentation.app import app

# test for usecase/task_service.py

@pytest.fixture
def repository():
    """Fixture for in-memory task repository."""
    return InMemoryTaskRepository()

@pytest.fixture
def task_service(repository):
    """Fixture for task service."""
    return TaskService(repository)

def test_create_task(task_service):
    """Test creating a task."""
    task = task_service.create_task(title="Test Task", description="This is a test task.")
    assert task.title == "Test Task"
    assert task.description == "This is a test task."
    assert not task.is_completed

def task_update(task_service):
    """Test updating a task."""
    task = task_service.create_task(title="Test Task", description="This is a test task.")
    updated_task = task_service.update_task(
        task_id=task.id,
        title="Updated Task",
        description="Updated description",
        is_completed=True)
    assert updated_task.title == "Updated Task"
    assert updated_task.description == "Updated description"
    assert updated_task.is_completed

def test_delete_task(task_service):
    """Test deleting a task."""
    task = task_service.create_task(title="Test Task", description="This is a test task.")
    task_service.delete_task(task.id)
    with pytest.raises(KeyError):
        task_service.get_task(task.id)

def test_list_tasks(task_service):
    """Test listing tasks."""
    task1 = task_service.create_task(title="Task 1", description="First task.")
    task2 = task_service.create_task(title="Task 2", description="Second task.")
    tasks = task_service.list_tasks()
    assert len(tasks) == 2
    assert task1 in tasks
    assert task2 in tasks


# test for presentation/app.py
client = TestClient(app)

def test_create_task_endpoint():
    """Test the create task endpoint."""
    response = client.post("/tasks/", json={"title": "Test Task", "description": "This is a test task."})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "This is a test task."
    assert not data["is_completed"]
    assert "id" in data

def task_get_non_existent_task_endpoint():
    """Test getting a non-existent task."""
    response = client.get("/tasks/non_existent_id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found"}

