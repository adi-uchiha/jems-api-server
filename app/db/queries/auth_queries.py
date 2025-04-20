from app.db.connection import get_db_connection
from psycopg2.extras import DictCursor
from app.schemas.auth import PasswordReset

async def get_user(username: str):
    query = """
        SELECT id, username, password, email, name 
        FROM users 
        WHERE username = %s
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(query, (username,))
            return cur.fetchone()

async def get_user_by_email(email: str):
    query = "SELECT * FROM users WHERE email = %s"
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(query, (email,))
            return cur.fetchone()

async def create_new_user(user_data: dict):
    query = """
        INSERT INTO users (username, password, email, name)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (
                user_data["username"],
                user_data["password"],
                user_data["email"],
                user_data["name"]
            ))
            conn.commit()
            return cur.fetchone()[0]

async def blacklist_token(token: str):
    query = """
        INSERT INTO token_blacklist (token, blacklisted_on)
        VALUES (%s, NOW())
    """
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (token,))
            conn.commit()

async def is_token_blacklisted(token: str) -> bool:
    query = "SELECT EXISTS(SELECT 1 FROM token_blacklist WHERE token = %s)"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (token,))
            return cur.fetchone()[0]

async def reset_user_password(email: str, new_password: str):
    query = "UPDATE users SET password = %s WHERE email = %s RETURNING id"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (new_password, email))
            result = cur.fetchone()
            if not result:
                raise ValueError("Email not found")
            conn.commit()
            return result[0]
