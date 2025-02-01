import logging

import sqlite3
from datetime import datetime

import os
from dotenv import load_dotenv

load_dotenv()  # .env を読み込む
db_path = os.getenv("DB_PATH")  # .env 内の DB_PATH を取得


# ログの設定
logging.basicConfig(
    level=logging.INFO,  # ログレベル（INFO, DEBUG, ERRORなど）
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),  # ファイルにログを書き込む
        logging.StreamHandler()  # コンソールにログを出力
    ]
)


class DBHelper:
    def __init__(self, db_path=db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        """Create necessary tables if they don't exist."""
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(post_id) REFERENCES posts(id),
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS likes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    FOREIGN KEY(post_id) REFERENCES posts(id),
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    UNIQUE(post_id, user_id)
                )
            ''')

    # User-related methods
    def create_user(self, username):
        """Create a new user."""
        created_at = datetime.utcnow().isoformat()
        with self.conn:
            cursor = self.conn.execute('''
                INSERT INTO users (username, created_at)
                VALUES (?, ?)
            ''', (username, created_at))
            return cursor.lastrowid

    def get_user(self, user_id):
        """Retrieve a user by ID."""
        cursor = self.conn.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        return cursor.fetchone()

    def get_all_users(self):
        """Retrieve all users."""
        cursor = self.conn.execute('SELECT * FROM users')
        return cursor.fetchall()

    def add_post(self, user_id, content):
        """新しいPostを追加し、ログを記録する"""
        created_at = datetime.utcnow().isoformat()
        logging.info(f"add_post called with user_id={user_id}, content={content}, created_at={created_at}")
        try:
            with self.conn:
                # SQLite のバージョンを確認
                cursor = self.conn.execute("SELECT sqlite_version();")
                sqlite_version = cursor.fetchone()
                logging.info(f"Connected to SQLite version: {sqlite_version[0]}")

                # データベース内のテーブル一覧を確認
                cursor = self.conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]  # 修正: row[0]でテーブル名を取得
                logging.info(f"Available tables: {tables}")

                # 'posts' テーブルの構造を確認
                cursor = self.conn.execute("PRAGMA table_info(posts);")
                columns = cursor.fetchall()
                logging.info(f"Table 'posts' structure: {columns}")

                # データを挿入
                cursor = self.conn.execute('''
                    INSERT INTO posts (user_id, content, created_at)
                    VALUES (?, ?, ?)
                ''', (user_id, content, created_at))
                self.conn.commit()  # コミットを明示的に実行
                post_id = cursor.lastrowid

                # 挿入直後にデータを確認
                cursor = self.conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
                post = cursor.fetchone()
                logging.info(f"Inserted post: {post}")

                # ログを記録
                logging.info(f"Post added: user_id={user_id}, content={content}, created_at={created_at}, post_id={post_id}")
                return post_id
        except Exception as e:
            # エラーログを記録
            logging.error(f"Failed to add post: user_id={user_id}, content={content}, error={str(e)}")
            raise


    def get_post(self, post_id):
        """Retrieve a post by ID."""
        cursor = self.conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
        return cursor.fetchone()

    def get_all_posts(self):
        """Retrieve all posts."""
        cursor = self.conn.execute('SELECT * FROM posts')
        return cursor.fetchall()

    # Comment-related methods
    def add_comment(self, post_id, user_id, content):
        """Add a comment to a post."""
        created_at = datetime.utcnow().isoformat()
        with self.conn:
            cursor = self.conn.execute('''
                INSERT INTO comments (post_id, user_id, content, created_at)
                VALUES (?, ?, ?, ?)
            ''', (post_id, user_id, content, created_at))
            return cursor.lastrowid

    def get_comments_for_post(self, post_id):
        """Retrieve all comments for a specific post."""
        cursor = self.conn.execute('SELECT * FROM comments WHERE post_id = ?', (post_id,))
        return cursor.fetchall()

    # Like-related methods
    def like_post(self, post_id, user_id):
        """Like a post."""
        with self.conn:
            self.conn.execute('''
                INSERT OR IGNORE INTO likes (post_id, user_id)
                VALUES (?, ?)
            ''', (post_id, user_id))

    def unlike_post(self, post_id, user_id):
        """Unlike a post."""
        with self.conn:
            self.conn.execute('''
                DELETE FROM likes WHERE post_id = ? AND user_id = ?
            ''', (post_id, user_id))

    def get_likes_for_post(self, post_id):
        """Get the count of likes for a specific post."""
        cursor = self.conn.execute('SELECT COUNT(*) as like_count FROM likes WHERE post_id = ?', (post_id,))
        return cursor.fetchone()["like_count"]

    def close(self):
        """Close the database connection."""
        self.conn.close()
