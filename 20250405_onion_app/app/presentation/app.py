# presentation/app.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from domain.entities import Task
from usecase.task_service import TaskService
from infrastructure.repository_impl import InMemoryTaskRepository
from infrastructure.repository_impl_postgres import SessionLocal, init_db, PostgresTaskRepository


app = FastAPI()

# 環境変数 REPOSITORY の値を確認し、利用するリポジトリを決定
repository_choice = os.getenv("REPOSITORY", "inmemory").lower()

if repository_choice == "postgres":
    # PostgreSQL を利用する場合
    init_db()  # テーブルの初期化
    session = SessionLocal()
    repository = PostgresTaskRepository(session)
else:
    # デフォルトは InMemory のモック実装を利用
    repository = InMemoryTaskRepository()

# 選択したリポジトリを使って TaskService を生成
task_service = TaskService(repository)

class TaskCreate(BaseModel):
    title: str = Field(..., example="Task Title")
    description: Optional[str] = Field(None, example="Task Description")
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, example="Updated Task Title")
    description: Optional[str] = Field(None, example="Updated Task Description")
    is_completed: Optional[bool] = Field(None, example=True)
class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    is_completed: bool
    created_at: str
    updated_at: str

def task_to_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        title=task.title,
        description=task.description,
        is_completed=task.is_completed,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat()
    )


@app.post("/tasks/", response_model=TaskResponse)
def create_task(task_create: TaskCreate):
    try:
        task = task_service.create_task(
            title=task_create.title,
            description=task_create.description
        )
        return task_to_response(task)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str):
    try:
        task = task_service.get_task(task_id)
        return task_to_response(task)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task_update: TaskUpdate):
    try:
        task = task_service.update_task(
            task_id,
            title=task_update.title,
            description=task_update.description,
            is_completed=task_update.is_completed
        )
        return task_to_response(task)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    try:
        task_service.delete_task(task_id)
        return {"detail": "Task deleted"}
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")

@app.get("/tasks/", response_model=List[TaskResponse])
def list_tasks():
    tasks = task_service.list_tasks()
    return [task_to_response(task) for task in tasks]