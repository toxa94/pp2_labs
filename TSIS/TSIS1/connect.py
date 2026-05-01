# connect.py — Database connection helper

import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG


def get_connection():
    """Return a new psycopg2 connection using settings from config.py."""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding('utf-8')
    return conn


def get_cursor(conn):
    """Return a RealDictCursor so rows come back as dicts."""
    return conn.cursor(cursor_factory=RealDictCursor)