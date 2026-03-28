import psycopg2
import csv
from config import DB_HOST, DB_NAME, DB_USER, DB_PASSWORD

# ================== CONNECTION ==================
conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)


# ================== TABLE ==================
def create_table():
    """Create contacts table if it doesn't exist"""
    query = """
    CREATE TABLE IF NOT EXISTS contacts (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        phone VARCHAR(20) NOT NULL
    )
    """
    with conn.cursor() as cur:
        cur.execute(query)
        conn.commit()


# ================== INSERT ==================
def insert_contact(name, phone):
    """Insert one contact"""
    query = "INSERT INTO contacts(name, phone) VALUES(%s, %s)"
    with conn.cursor() as cur:
        cur.execute(query, (name, phone))
        conn.commit()


def insert_from_console():
    """Insert contact from user input"""
    name = input("👤 Name: ")
    phone = input("📞 Phone: ")

    insert_contact(name, phone)
    print("✅ Contact added!")


def insert_from_csv(filename):
    """Import contacts from CSV file"""
    query = "INSERT INTO contacts(name, phone) VALUES(%s, %s)"

    with conn.cursor() as cur:
        with open(filename, "r") as file:
            reader = csv.reader(file)
            next(reader)  # skip header

            for row in reader:
                name, phone = row
                cur.execute(query, (name, phone))

        conn.commit()

    print(f"📂 Imported from {filename}")


# ================== SELECT ==================
def get_all_contacts():
    """Return all contacts"""
    query = "SELECT * FROM contacts ORDER BY name"

    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def search_contacts(pattern):
    """Search by name or phone"""
    query = """
    SELECT * FROM contacts
    WHERE name ILIKE %s OR phone ILIKE %s
    """

    like = f"%{pattern}%"

    with conn.cursor() as cur:
        cur.execute(query, (like, like))
        return cur.fetchall()


# ================== UPDATE ==================
def update_phone(name, new_phone):
    """Update phone by name"""
    query = "UPDATE contacts SET phone=%s WHERE name=%s"

    with conn.cursor() as cur:
        cur.execute(query, (new_phone, name))
        conn.commit()

        print(f"🔄 Updated {cur.rowcount} contact(s)")


def update_name(phone, new_name):
    """Update name by phone"""
    query = "UPDATE contacts SET name=%s WHERE phone=%s"

    with conn.cursor() as cur:
        cur.execute(query, (new_name, phone))
        conn.commit()

        print(f"🔄 Updated {cur.rowcount} contact(s)")


# ================== DELETE ==================
def delete_by_name(name):
    """Delete contact by name"""
    query = "DELETE FROM contacts WHERE name=%s"

    with conn.cursor() as cur:
        cur.execute(query, (name,))
        conn.commit()

        print(f"🗑 Deleted {cur.rowcount} contact(s)")


def delete_by_phone(phone):
    """Delete contact by phone"""
    query = "DELETE FROM contacts WHERE phone=%s"

    with conn.cursor() as cur:
        cur.execute(query, (phone,))
        conn.commit()

        print(f"🗑 Deleted {cur.rowcount} contact(s)")


# ================== DISPLAY ==================
def print_contacts(contacts):
    """Pretty print contacts"""
    if not contacts:
        print("❌ No contacts found")
        return

    print("\n📋 CONTACT LIST:")
    print("-" * 30)

    for c in contacts:
        print(f"ID: {c[0]} | Name: {c[1]} | Phone: {c[2]}")

    print("-" * 30)


# ================== MENU ==================
def main():
    create_table()

    while True:
        print("\n📱 PHONEBOOK MENU")
        print("1 - Show all contacts")
        print("2 - Add contact")
        print("3 - Import from CSV")
        print("4 - Search")
        print("5 - Update phone by name")
        print("6 - Update name by phone")
        print("7 - Delete by name")
        print("8 - Delete by phone")
        print("0 - Exit")

        choice = input("\n👉 Choose: ")

        if choice == "1":
            print_contacts(get_all_contacts())

        elif choice == "2":
            insert_from_console()

        elif choice == "3":
            insert_from_csv("Practice-07/contacts.csv")

        elif choice == "4":
            pattern = input("Search: ")
            print_contacts(search_contacts(pattern))

        elif choice == "5":
            name = input("Name: ")
            new_phone = input("New phone: ")
            update_phone(name, new_phone)

        elif choice == "6":
            phone = input("Phone: ")
            new_name = input("New name: ")
            update_name(phone, new_name)

        elif choice == "7":
            name = input("Name: ")
            delete_by_name(name)

        elif choice == "8":
            phone = input("Phone: ")
            delete_by_phone(phone)

        elif choice == "0":
            break

        else:
            print("❌ Invalid choice")

    conn.close()
    print("👋 Goodbye!")


if __name__ == "__main__":
    main()