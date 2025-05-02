# domain/ports.py
from abc import ABC, abstractmethod
from domain.models import User

class UserRepository(ABC):
    @abstractmethod
    def save(self, user: User): pass

class NotificationService(ABC):
    @abstractmethod
    def send_welcome_email(self, user: User): pass