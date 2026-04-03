import psycopg2
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD


def connect():
    try:
        return psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=5432
        )
    except Exception as e:
        print("❌ Connection error:", e)
        return None