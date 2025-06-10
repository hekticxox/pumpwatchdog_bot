import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("users.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    token TEXT UNIQUE,
    expiry DATETIME
)
""")

# Example token
token = "testtoken123"
expiry = (datetime.now() + timedelta(days=7)).isoformat()
cur.execute("INSERT OR IGNORE INTO users (token, expiry) VALUES (?, ?)", (token, expiry))

conn.commit()
conn.close()

