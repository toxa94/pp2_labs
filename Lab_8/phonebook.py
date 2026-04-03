import psycopg2
from config import load_config


# ================== CONNECTION ==================
def get_conn():
    config = load_config()
    return psycopg2.connect(**config)


# ================== TABLE ==================
def create_table():
    query = """
    CREATE TABLE IF NOT EXISTS phonebook (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        phone VARCHAR(20) NOT NULL
    )
    """

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()

    print("✅ Table ready")


# ================== UPSERT ==================
def upsert_user():
    name = input("👤 Name: ")
    phone = input("📞 Phone: ")

    query = "CALL upsert_u(%s, %s)"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (name, phone))
            conn.commit()

    print("✅ User added/updated")


# ================== BULK INSERT ==================
def insert_many():
    print("👥 Enter usernames:")
    users = input().split()

    print("📞 Enter phones:")
    phones = input().split()

    if len(users) != len(phones):
        print("❌ Error: sizes do not match")
        return

    with get_conn() as conn:
        conn.notices.clear()

        with conn.cursor() as cur:
            cur.execute("CALL loophz(%s, %s)", (users, phones))
            conn.commit()

        # show notices
        for notice in conn.notices:
            print("⚠️", notice.strip())

    print("✅ Done")


# ================== SEARCH ==================
def search_contacts():
    pattern = input("🔍 Search: ")

    query = "SELECT * FROM records(%s)"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (pattern,))
            rows = cur.fetchall()

    print_contacts(rows)


# ================== PAGINATION ==================
def pagination():
    try:
        limit = int(input("📄 Limit: "))
        offset = int(input("➡️ Offset: "))
    except:
        print("❌ Numbers only")
        return

    query = "SELECT * FROM pagination(%s, %s)"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (limit, offset))
            rows = cur.fetchall()

    print_contacts(rows)


# ================== DELETE ==================
def delete_contact():
    print("1 - Delete by name")
    print("2 - Delete by phone")

    choice = input("👉 Choose: ")

    if choice == "1":
        value = input("👤 Name: ")
    elif choice == "2":
        value = input("📞 Phone: ")
    else:
        print("❌ Wrong choice")
        return

    query = "CALL del_user(%s)"

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (value,))
            conn.commit()

    print("🗑 Deleted")


# ================== DISPLAY ==================
def print_contacts(rows):
    if not rows:
        print("❌ No data")
        return

    print("\n📋 CONTACTS:")
    print("-" * 35)

    for r in rows:
        print(f"ID: {r[0]} | Name: {r[1]} | Phone: {r[2]}")

    print("-" * 35)


# ================== MENU ==================
def main():
    create_table()

    while True:
        print("\n📱 PHONEBOOK MENU")
        print("1 - Upsert user")
        print("2 - Insert many")
        print("3 - Search")
        print("4 - Pagination")
        print("5 - Delete")
        print("0 - Exit")

        choice = input("\n👉 Choose: ")

        if choice == "1":
            upsert_user()

        elif choice == "2":
            insert_many()

        elif choice == "3":
            search_contacts()

        elif choice == "4":
            pagination()

        elif choice == "5":
            delete_contact()

        elif choice == "0":
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    main()