import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

DB_PATH = "users.db"

def create_users_table():
    """
    Create the users table if it does not exist.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            token TEXT NOT NULL,
            expiry DATETIME NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def generate_token(username: str) -> str:
    """
    Generate a secure token for a user.
    """
    raw = f"{username}:{secrets.token_urlsafe(32)}"
    return hashlib.sha256(raw.encode()).hexdigest()

def add_user(username: str, days_valid: int = 30) -> Optional[str]:
    """
    Add a new user with a unique token and expiry.
    Returns the token if added, or None if user exists.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    expiry = (datetime.utcnow() + timedelta(days=days_valid)).strftime("%Y-%m-%d %H:%M:%S")
    token = generate_token(username)
    try:
        cur.execute("INSERT INTO users (username, token, expiry) VALUES (?, ?, ?)",
                    (username, token, expiry))
        conn.commit()
        return token
    except sqlite3.IntegrityError:
        # User already exists
        return None
    finally:
        conn.close()

def get_user_token(username: str) -> Optional[str]:
    """
    Retrieve the token for a given username.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT token FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def is_valid_token(token: str) -> bool:
    """
    Check if the token exists and is not expired.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT expiry FROM users WHERE token=?", (token,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    expiry_str = row[0]
    expiry = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
    return expiry > datetime.utcnow()

def renew_token(username: str, days_valid: int = 30) -> bool:
    """
    Extend a user's token expiry.
    Returns True if successful, False otherwise.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    expiry = (datetime.utcnow() + timedelta(days=days_valid)).strftime("%Y-%m-%d %H:%M:%S")
    try:
        cur.execute("UPDATE users SET expiry=? WHERE username=?", (expiry, username))
        updated = cur.rowcount
        conn.commit()
        return updated > 0
    finally:
        conn.close()

def delete_user(username: str) -> bool:
    """
    Delete a user from the database.
    Returns True if deleted, False if user was not found.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE username=?", (username,))
        deleted = cur.rowcount
        conn.commit()
        return deleted > 0
    finally:
        conn.close()

if __name__ == "__main__":
    # Example usage
    create_users_table()
    user = "testuser"
    print("Adding user:", user)
    token = add_user(user)
    if token:
        print(f"User {user} added with token: {token}")
    else:
        print(f"User {user} already exists. Token: {get_user_token(user)}")
    print("Is valid token?", is_valid_token(get_user_token(user)))
    print("Renewing token:", renew_token(user, 60))
    print("Deleting user:", delete_user(user))