# tests/test_user_service.py
import pytest
from application.user_service import UserService
from domain.models import User

# テスト用のモッククラス
class FakeUserRepository:
    def __init__(self):
        self.saved_users = []

    def save(self, user: User):
        self.saved_users.append(user)

class FakeNotificationService:
    def __init__(self):
        self.sent_emails = []

    def send_welcome_email(self, user: User):
        self.sent_emails.append(user)

def test_register_user_success():
    repo = FakeUserRepository()
    notifier = FakeNotificationService()
    service = UserService(repo, notifier)

    result = service.register_user("Keita", "keita@example.com")

    assert result.name == "Keita"
    assert result.email == "keita@example.com"
    assert repo.saved_users == [result]
    assert notifier.sent_emails == [result]


class FailingRepo:
    def save(self, user: User):
        raise ValueError("Duplicate email")

def test_register_user_duplicate_email():
    repo = FailingRepo()
    notifier = FakeNotificationService()
    service = UserService(repo, notifier)

    with pytest.raises(ValueError):
        service.register_user("Keita", "keita@example.com")