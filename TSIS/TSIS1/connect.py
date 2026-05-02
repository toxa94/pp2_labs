import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG


def get_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding('UTF8')  # ← исправлено
    return conn


def get_cursor(conn):
    return conn.cursor(cursor_factory=RealDictCursor)