from fastapi import FastAPI, Request, HTTPException
import sqlite3
import json
import logging
from typing import Optional

app = FastAPI()

# Configure logging
logging.basicConfig(
    filename="pump_signals_api.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def validate_token(token: str) -> bool:
    """
    Validate the API token from the users database.
    Args:
        token (str): API token.
    Returns:
        bool: True if valid and not expired, False otherwise.
    """
    try:
        conn = sqlite3.connect("users.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE token=? AND expiry > datetime('now')", (token,))
        result = cur.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        logging.error(f"Token validation error: {e}")
        return False

def read_signals(path: str = "signals.json") -> Optional[dict]:
    """
    Read signals from the signals JSON file.
    Args:
        path (str): Path to signals file.
    Returns:
        dict or None: Signal data or None if error.
    """
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error reading signals file ({path}): {e}")
        return None

@app.get("/signal/latest")
async def get_signal(request: Request):
    """
    Get the latest signals.
    Requires Bearer token in Authorization header.
    """
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        logging.warning("Missing or malformed token in request.")
        raise HTTPException(status_code=401, detail="Token missing or malformed")
    
    if not validate_token(token[7:]):
        logging.warning("Invalid or expired token attempted.")
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    signals = read_signals()
    if signals is None:
        raise HTTPException(status_code=500, detail="Could not read signals data")
    return signals

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
