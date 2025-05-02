# adapters/email_notifier.py
from domain.ports import NotificationService
from domain.models import User

class ConsoleEmailNotifier(NotificationService):
    def send_welcome_email(self, user: User):
        print(f"[Email] Sent to {user.email}: Welcome, {user.name}!")