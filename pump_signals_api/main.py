from fastapi import FastAPI, Request, HTTPException
import sqlite3
import json

app = FastAPI()

def validate_token(token: str):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE token=? AND expiry > datetime('now')", (token,))
    result = cur.fetchone()
    conn.close()
    return result is not None

@app.get("/signal/latest")
async def get_signal(request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing")
    
    if not validate_token(token[7:]):
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    with open("signals.json") as f:
        return json.load(f)
