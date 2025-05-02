# adapters/fastapi_controller.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from application.user_service import UserService
from domain.ports import UserRepository, NotificationService

class UserRequest(BaseModel):
    name: str
    email: str

def get_user_service(
    repo: UserRepository,
    notifier: NotificationService
):
    return UserService(repo, notifier)

def create_user_router(user_service: UserService):
    router = APIRouter()

    @router.post("/users")
    def register(user: UserRequest):
        result = user_service.register_user(user.name, user.email)
        return {"message": f"User {result.name} registered successfully"}

    return router