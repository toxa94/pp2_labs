# connect.py — Database connection helper

import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG


def get_connection():
    """Return a new psycopg2 connection using settings from config.py."""
    return psycopg2.connect(**DB_CONFIG)


def get_cursor(conn):
    """Return a RealDictCursor so rows come back as dicts."""
    return conn.cursor(cursor_factory=RealDictCursor)