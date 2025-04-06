# infrastructure/repository_impl_postgres.py

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from domain.entities import Task
from domain.repositories import TaskRepository

# SQLAlchemy の宣言的ベースクラスを作成
Base = declarative_base()

# ORM 用の Task モデル
class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_completed = Column(Boolean, default=False)

    def to_entity(self) -> Task:
        """
        ORM モデルからドメインの Task エンティティに変換するヘルパーメソッド
        """
        return Task(
            id=self.id,
            title=self.title,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_completed=self.is_completed
        )

    @staticmethod
    def from_entity(task: Task) -> "TaskModel":
        """
        ドメインの Task エンティティから ORM モデルに変換するヘルパーメソッド
        """
        return TaskModel(
            id=task.id,
            title=task.title,
            description=task.description,
            created_at=task.created_at,
            updated_at=task.updated_at,
            is_completed=task.is_completed
        )


class PostgresTaskRepository(TaskRepository):
    """
    PostgresTaskRepository は、Docker上のPostgreSQLを利用してタスクを永続化する実装です。
    TaskRepository インターフェースを実装し、SQLAlchemy を利用してデータベースとやりとりします。
    """

    def __init__(self, session: Session):
        self.session = session

    def add(self, task: Task) -> None:
        task_model = TaskModel.from_entity(task)
        self.session.add(task_model)
        self.session.commit()

    def get(self, task_id: str) -> Task:
        task_model = self.session.query(TaskModel).filter_by(id=task_id).first()
        if task_model is None:
            raise KeyError(f"Task with id {task_id} not found")
        return task_model.to_entity()

    def update(self, task: Task) -> None:
        task_model = self.session.query(TaskModel).filter_by(id=task.id).first()
        if task_model is None:
            raise KeyError(f"Task with id {task.id} not found")
        # 更新内容を設定
        task_model.title = task.title
        task_model.description = task.description
        task_model.is_completed = task.is_completed
        task_model.updated_at = datetime.utcnow()
        self.session.commit()

    def delete(self, task_id: str) -> None:
        task_model = self.session.query(TaskModel).filter_by(id=task_id).first()
        if task_model is None:
            raise KeyError(f"Task with id {task_id} not found")
        self.session.delete(task_model)
        self.session.commit()

    def list_all(self) -> List[Task]:
        task_models = self.session.query(TaskModel).all()
        return [tm.to_entity() for tm in task_models]


# --- データベース接続とセッションの設定 ---

# PostgreSQL への接続文字列（Dockerで立てたPostgreSQLの設定に合わせる）
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/onion_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    データベーステーブルの作成。初回実行時に呼び出します。
    """
    Base.metadata.create_all(bind=engine)

# 初期化処理（必要な場合に実行）
if __name__ == "__main__":
    init_db()

