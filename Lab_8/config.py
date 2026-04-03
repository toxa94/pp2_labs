# Database connection parameters
# Keep these in a separate file so they're easy to change
# and not scattered across your code

DB_HOST = "localhost"
DB_NAME = "phonebook"
DB_USER = "postgres"
DB_PASSWORD = "123456"

def load_config():
    return {
        "host": DB_HOST,
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "port": 5432
    }