# adapters/sqlite_repository.py
import sqlite3
from domain.models import User
from domain.ports import UserRepository

class SQLiteUserRepository(UserRepository):
    def __init__(self, db_path="users.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("CREATE TABLE IF NOT EXISTS users (name TEXT, email TEXT)")

    def save(self, user: User):
        self.conn.execute("INSERT INTO users (name, email) VALUES (?, ?)", (user.name, user.email))
        self.conn.commit()
