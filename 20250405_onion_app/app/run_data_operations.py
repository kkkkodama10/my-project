# run_data_operations.py

from infrastructure.repository_impl_postgres import SessionLocal, init_db, PostgresTaskRepository
from usecase.task_service import TaskService

def main():
    # 1. データベースの初期化（テーブル作成）
    init_db()
    
    # 2. セッションを生成して、PostgresTaskRepository と TaskService を構築
    session = SessionLocal()
    repository = PostgresTaskRepository(session)
    task_service = TaskService(repository)
    
    # 3. タスクの作成
    print(">> タスクを作成します")
    task = task_service.create_task(title="Test kodama", description="This is a test task for PostgreSQL.")
    print(f"作成されたタスク: {task}")
    
    # 4. タスク一覧の取得
    print("\n>> タスク一覧を取得します")
    tasks = task_service.list_tasks()
    for t in tasks:
        print(t)
    
    # 5. タスクの更新
    print("\n>> タスクを更新します")
    updated_task = task_service.update_task(
        task_id=task.id, 
        title="Updated Test Task", 
        description="Updated description", 
        is_completed=True
    )
    print(f"更新後のタスク: {updated_task}")
    
    # 6. タスクの削除
    print("\n>> タスクを削除します")
    task_service.delete_task(task.id)
    print("タスクが削除されました")
    
    # 7. 削除後のタスク一覧を取得
    print("\n>> 削除後のタスク一覧")
    tasks = task_service.list_tasks()
    if not tasks:
        print("現在、タスクは存在しません")
    else:
        for t in tasks:
            print(t)

if __name__ == "__main__":
    main()
