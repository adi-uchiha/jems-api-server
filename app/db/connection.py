import os
from psycopg2 import pool
from app.core.config import settings
import contextlib
from dotenv import load_dotenv

connection_pool = None

def init_connection_pool():
    global connection_pool
    if connection_pool is None:
        try:
            connection_pool = pool.SimpleConnectionPool(
                **settings.database_config
            )
            print("✅Database pool initialized successfully✅")
        except Exception as e:
            print(f"Error creating connection pool: {e}")
            raise

@contextlib.contextmanager
def get_db_connection():
    """Get a database connection from the pool"""
    if connection_pool is None:
        init_connection_pool()
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

def close_all_db_connections():
    """Close all connections in the pool"""
    if connection_pool:
        print("🚫Closing all database connections in the pool🚫")
        connection_pool.closeall()

import atexit
atexit.register(close_all_db_connections)
