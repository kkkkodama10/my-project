# application/user_service.py
from domain.models import User
from domain.ports import UserRepository, NotificationService

class UserService:
    def __init__(self, repo: UserRepository, notifier: NotificationService):
        self.repo = repo
        self.notifier = notifier

    def register_user(self, name: str, email: str):
        user = User(name, email)
        self.repo.save(user)
        self.notifier.send_welcome_email(user)
        return user
