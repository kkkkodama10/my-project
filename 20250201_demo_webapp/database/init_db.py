import sqlite3
from datetime import datetime

# データベースファイルのパス
DATABASE = "sns_app.db"

def init_db():
    # データベース接続
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Usersテーブル作成
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Postsテーブル作成
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users (id)
    );
    """)

    # Likesテーブル作成
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users (id),
        FOREIGN KEY (post_id) REFERENCES Posts (id)
    );
    """)

    # 確定して接続を閉じる
    conn.commit()
    conn.close()

    print(f"Database initialized at {DATABASE}")

if __name__ == "__main__":
    init_db()

