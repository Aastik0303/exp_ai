"""
Authentication module with bcrypt password hashing.
Handles user signup, login and session management.
"""

import bcrypt
from db import get_connection


def hash_password(password: str) -> str:
    """Hash password using bcrypt with salt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against stored hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def signup_user(username: str, password: str):
    """Register a new user with validation."""
    if not username or not password:
        return False, "Username and password are required."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."
    if not username.isalnum():
        return False, "Username must contain only letters and numbers."

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username.lower(), hash_password(password)),
        )
        conn.commit()
        return True, "Signup successful! Please log in."
    except Exception as e:
        if "UNIQUE" in str(e):
            return False, "Username already exists. Try another one."
        return False, f"Error: {str(e)}"
    finally:
        conn.close()


def login_user(username: str, password: str):
    """Authenticate user and check if active."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username.lower(),))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return False, None

    if not verify_password(password, user["password"]):
        return False, None

    # Check if user is active
    if not user["is_active"]:
        return False, "deactivated"

    return True, dict(user)
