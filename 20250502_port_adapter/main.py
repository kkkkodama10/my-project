# main.py
from fastapi import FastAPI
from adapters.sqlite_repository import SQLiteUserRepository
from adapters.email_notifier import ConsoleEmailNotifier
from adapters.fastapi_controller import create_user_router
from application.user_service import UserService

app = FastAPI()

# Adapterの実装をここで注入
repo = SQLiteUserRepository()
notifier = ConsoleEmailNotifier()
service = UserService(repo, notifier)

# ルーターにサービスを注入してマウント
user_router = create_user_router(service)
app.include_router(user_router)
