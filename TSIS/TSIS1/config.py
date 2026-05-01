# config.py — Database connection configuration
# Update these values to match your PostgreSQL setup

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "phonebook_db",
    "user":     "postgres",
    "password": "123456",
}

# Pagination: contacts displayed per page
PAGE_SIZE = 5