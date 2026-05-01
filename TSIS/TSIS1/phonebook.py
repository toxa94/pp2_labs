# phonebook.py — PhoneBook Extended Contact Management (TSIS1)
# Requires: psycopg2, Python 3.8+
# Run: python phonebook.py

import csv
import json
import sys
from datetime import date, datetime

from config import PAGE_SIZE
from connect import get_connection, get_cursor

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _serialize(obj):
    """JSON serialiser for date/datetime objects."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serialisable")


def _print_contacts(rows):
    """Pretty-print a list of contact dicts."""
    if not rows:
        print("  (no contacts found)")
        return
    print()
    for r in rows:
        print(f"  [{r['id']}] {r['name']}")
        print(f"       Email   : {r.get('email') or '—'}")
        bday = r.get('birthday')
        print(f"       Birthday: {bday.isoformat() if bday else '—'}")
        print(f"       Group   : {r.get('group_name') or '—'}")
        # phones may come as a string from the DB function or a list from Python
        phones = r.get('phones') or r.get('phone_list') or '—'
        if isinstance(phones, list):
            phones = ', '.join(f"{p['phone']} ({p['type']})" for p in phones)
        print(f"       Phones  : {phones}")
    print()


def _ask(prompt, choices=None):
    """Read a non-empty line from stdin; optionally validate against choices."""
    while True:
        val = input(prompt).strip()
        if not val:
            continue
        if choices and val.lower() not in choices:
            print(f"  Please enter one of: {', '.join(choices)}")
            continue
        return val


# ─────────────────────────────────────────────────────────────────────────────
# Schema & Procedure Initialisation
# ─────────────────────────────────────────────────────────────────────────────

def init_db():
    """Apply schema.sql and procedures.sql to the connected database."""
    conn = get_connection()
    try:
        with conn:
            with get_cursor(conn) as cur:
                for filename in ("schema.sql", "procedures.sql"):
                    with open(filename, "r") as fh:
                        sql = fh.read()
                    cur.execute(sql)
        print("✓ Database initialised (schema + procedures applied).")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Section 3.4 — Stored Procedure Callers
# ─────────────────────────────────────────────────────────────────────────────

def call_add_phone(contact_name: str, phone: str, phone_type: str):
    """Call the add_phone stored procedure."""
    conn = get_connection()
    try:
        with conn:
            with get_cursor(conn) as cur:
                cur.execute(
                    "CALL add_phone(%s, %s, %s)",
                    (contact_name, phone, phone_type)
                )
        print(f"✓ Phone {phone} ({phone_type}) added to '{contact_name}'.")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        conn.close()


def call_move_to_group(contact_name: str, group_name: str):
    """Call the move_to_group stored procedure."""
    conn = get_connection()
    try:
        with conn:
            with get_cursor(conn) as cur:
                cur.execute(
                    "CALL move_to_group(%s, %s)",
                    (contact_name, group_name)
                )
        print(f"✓ '{contact_name}' moved to group '{group_name}'.")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        conn.close()


def call_search_contacts(query: str):
    """Call the search_contacts DB function and display results."""
    conn = get_connection()
    try:
        with get_cursor(conn) as cur:
            cur.execute("SELECT * FROM search_contacts(%s)", (query,))
            rows = cur.fetchall()
        _print_contacts(rows)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Section 3.2 — Advanced Console Search & Filter
# ─────────────────────────────────────────────────────────────────────────────

def _build_list_query(group_filter=None, email_filter=None, sort_by="name"):
    """
    Construct the SELECT for the contacts list view.
    Returns (sql_string, params_tuple).
    """
    # Map user-facing sort choices to SQL expressions
    sort_map = {
        "name":    "c.name ASC",
        "birthday":"c.birthday ASC NULLS LAST",
        "date":    "c.created_at ASC NULLS LAST",
    }
    order_clause = sort_map.get(sort_by, "c.name ASC")

    sql = """
        SELECT
            c.id,
            c.name,
            c.email,
            c.birthday,
            c.created_at,
            g.name                                              AS group_name,
            STRING_AGG(p.phone || ' (' || p.type || ')', ', ') AS phones
        FROM  contacts c
        LEFT  JOIN groups g ON g.id = c.group_id
        LEFT  JOIN phones p ON p.contact_id = c.id
        WHERE 1=1
    """
    params = []

    if group_filter:
        sql += " AND LOWER(g.name) = LOWER(%s)"
        params.append(group_filter)

    if email_filter:
        sql += " AND LOWER(c.email) LIKE %s"
        params.append(f"%{email_filter.lower()}%")

    sql += f" GROUP BY c.id, c.name, c.email, c.birthday, c.created_at, g.name"
    sql += f" ORDER BY {order_clause}"

    return sql, tuple(params)


def paginated_browse():
    """
    Interactive paginated contact browser.
    Supports: filter by group, search by email, sort, next/prev/quit.
    """
    print("\n─── Browse Contacts ───")

    # Gather filter / sort preferences
    group_filter = input("Filter by group (leave blank for all): ").strip() or None
    email_filter = input("Search by email (leave blank for all): ").strip() or None
    sort_by = _ask(
        "Sort by [name / birthday / date]: ",
        choices=["name", "birthday", "date"]
    )

    base_sql, params = _build_list_query(group_filter, email_filter, sort_by)

    conn = get_connection()
    offset = 0
    try:
        while True:
            paginated_sql = base_sql + f" LIMIT {PAGE_SIZE} OFFSET {offset}"
            with get_cursor(conn) as cur:
                cur.execute(paginated_sql, params)
                rows = cur.fetchall()

            page_num = offset // PAGE_SIZE + 1
            print(f"\n── Page {page_num} ──")
            _print_contacts(rows)

            # Navigation prompt
            has_prev = offset > 0
            has_next = len(rows) == PAGE_SIZE
            nav_opts = []
            if has_prev:
                nav_opts.append("prev")
            if has_next:
                nav_opts.append("next")
            nav_opts.append("quit")

            choice = _ask(f"[{' / '.join(nav_opts)}]: ", choices=nav_opts)
            if choice == "next":
                offset += PAGE_SIZE
            elif choice == "prev":
                offset = max(0, offset - PAGE_SIZE)
            else:
                break
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Section 3.3 — Import / Export
# ─────────────────────────────────────────────────────────────────────────────

def export_to_json(filepath: str = "contacts_export.json"):
    """
    Export all contacts with their phones and group to a JSON file.
    """
    conn = get_connection()
    try:
        with get_cursor(conn) as cur:
            # Fetch all contacts
            cur.execute("""
                SELECT c.id, c.name, c.email, c.birthday, c.created_at,
                       g.name AS group_name
                FROM   contacts c
                LEFT   JOIN groups g ON g.id = c.group_id
                ORDER  BY c.name
            """)
            contacts = [dict(r) for r in cur.fetchall()]

            # Attach phones list to each contact
            for contact in contacts:
                cur.execute(
                    "SELECT phone, type FROM phones WHERE contact_id = %s ORDER BY id",
                    (contact["id"],)
                )
                contact["phone_list"] = [dict(p) for p in cur.fetchall()]
                # Remove internal id from export
                del contact["id"]

        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(contacts, fh, indent=2, default=_serialize, ensure_ascii=False)

        print(f"✓ {len(contacts)} contacts exported → {filepath}")
    finally:
        conn.close()


def _upsert_contact(cur, name: str, email, birthday, group_name,
                    phone_list: list, overwrite: bool):
    """
    Insert or update a single contact during JSON import.
    phone_list: [{"phone": "...", "type": "..."}]
    """
    # Resolve group
    group_id = None
    if group_name:
        cur.execute(
            "SELECT id FROM groups WHERE LOWER(name) = LOWER(%s)", (group_name,)
        )
        row = cur.fetchone()
        if row:
            group_id = row["id"]
        else:
            cur.execute(
                "INSERT INTO groups (name) VALUES (%s) RETURNING id", (group_name,)
            )
            group_id = cur.fetchone()["id"]

    # Check for existing contact
    cur.execute("SELECT id FROM contacts WHERE LOWER(name) = LOWER(%s)", (name,))
    existing = cur.fetchone()

    if existing:
        if not overwrite:
            return False  # caller will skip
        # Overwrite: update fields
        cur.execute("""
            UPDATE contacts
            SET    email = %s, birthday = %s, group_id = %s
            WHERE  id    = %s
        """, (email, birthday, group_id, existing["id"]))
        contact_id = existing["id"]
        # Remove old phones so we replace them cleanly
        cur.execute("DELETE FROM phones WHERE contact_id = %s", (contact_id,))
    else:
        # New contact
        cur.execute("""
            INSERT INTO contacts (name, email, birthday, group_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (name, email, birthday, group_id))
        contact_id = cur.fetchone()["id"]

    # Insert phones
    for ph in phone_list:
        cur.execute(
            "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
            (contact_id, ph.get("phone"), ph.get("type", "mobile"))
        )
    return True


def import_from_json(filepath: str = "contacts_export.json"):
    """
    Import contacts from a JSON file.
    On duplicate name: asks user to skip or overwrite (once for all duplicates).
    """
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        print(f"✗ File not found: {filepath}")
        return

    # Ask duplicate strategy up front
    dup_strategy = _ask(
        "On duplicate name — skip or overwrite? [skip/overwrite]: ",
        choices=["skip", "overwrite"]
    )
    overwrite = dup_strategy == "overwrite"

    inserted = skipped = 0
    conn = get_connection()
    try:
        with conn:
            with get_cursor(conn) as cur:
                for item in data:
                    ok = _upsert_contact(
                        cur,
                        name       = item.get("name", ""),
                        email      = item.get("email"),
                        birthday   = item.get("birthday"),
                        group_name = item.get("group_name"),
                        phone_list = item.get("phone_list", []),
                        overwrite  = overwrite,
                    )
                    if ok:
                        inserted += 1
                    else:
                        skipped += 1
        print(f"✓ Import done — inserted/updated: {inserted}, skipped: {skipped}")
    finally:
        conn.close()


def import_from_csv(filepath: str = "contacts.csv"):
    """
    Extended CSV import supporting columns:
        name, phone, type, email, birthday, group
    """
    try:
        fh = open(filepath, newline="", encoding="utf-8")
    except FileNotFoundError:
        print(f"✗ File not found: {filepath}")
        return

    inserted = errors = 0
    conn = get_connection()
    try:
        with conn:
            with get_cursor(conn) as cur:
                reader = csv.DictReader(fh)
                for row in reader:
                    name  = (row.get("name") or "").strip()
                    phone = (row.get("phone") or "").strip()
                    ptype = (row.get("type") or "mobile").strip()
                    email = (row.get("email") or "").strip() or None
                    bday  = (row.get("birthday") or "").strip() or None
                    group = (row.get("group") or "").strip() or None

                    if not name:
                        errors += 1
                        continue

                    phone_list = [{"phone": phone, "type": ptype}] if phone else []

                    try:
                        _upsert_contact(
                            cur,
                            name       = name,
                            email      = email,
                            birthday   = bday,
                            group_name = group,
                            phone_list = phone_list,
                            overwrite  = False,   # CSV: never overwrite silently
                        )
                        inserted += 1
                    except Exception as e:
                        print(f"  Row error ({name}): {e}")
                        errors += 1
        print(f"✓ CSV import done — inserted: {inserted}, errors: {errors}")
    finally:
        fh.close()
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Interactive console menus
# ─────────────────────────────────────────────────────────────────────────────

def menu_search():
    print("\n─── Search & Filter ───")
    print("  1. Full-text search (name / email / phone)  [DB function]")
    print("  2. Browse with filters & pagination")
    print("  0. Back")
    choice = _ask("Choice: ", choices=["0", "1", "2"])

    if choice == "1":
        q = input("Enter search term: ").strip()
        if q:
            call_search_contacts(q)
    elif choice == "2":
        paginated_browse()


def menu_phones():
    print("\n─── Phone Management ───")
    print("  1. Add phone to contact  [add_phone procedure]")
    print("  0. Back")
    choice = _ask("Choice: ", choices=["0", "1"])

    if choice == "1":
        cname = input("Contact name: ").strip()
        phone = input("Phone number: ").strip()
        ptype = _ask("Type [home/work/mobile]: ", choices=["home", "work", "mobile"])
        call_add_phone(cname, phone, ptype)


def menu_groups():
    print("\n─── Group Management ───")
    print("  1. Move contact to group  [move_to_group procedure]")
    print("  0. Back")
    choice = _ask("Choice: ", choices=["0", "1"])

    if choice == "1":
        cname  = input("Contact name: ").strip()
        gname  = input("Group name (Family/Work/Friend/Other or new): ").strip()
        call_move_to_group(cname, gname)


def menu_import_export():
    print("\n─── Import / Export ───")
    print("  1. Export to JSON")
    print("  2. Import from JSON")
    print("  3. Import from CSV (extended)")
    print("  0. Back")
    choice = _ask("Choice: ", choices=["0", "1", "2", "3"])

    if choice == "1":
        path = input("Output file [contacts_export.json]: ").strip() or "contacts_export.json"
        export_to_json(path)
    elif choice == "2":
        path = input("Input file [contacts_export.json]: ").strip() or "contacts_export.json"
        import_from_json(path)
    elif choice == "3":
        path = input("Input CSV [contacts.csv]: ").strip() or "contacts.csv"
        import_from_csv(path)


def main_menu():
    print("\n╔══════════════════════════════════╗")
    print("║   PhoneBook — Extended (TSIS1)   ║")
    print("╚══════════════════════════════════╝")
    print("  1. Search & Filter contacts")
    print("  2. Phone number management")
    print("  3. Group management")
    print("  4. Import / Export")
    print("  5. Initialise / reset database schema")
    print("  0. Exit")
    return _ask("Choice: ", choices=["0", "1", "2", "3", "4", "5"])


def main():
    while True:
        choice = main_menu()
        if choice == "0":
            print("Goodbye!")
            sys.exit(0)
        elif choice == "1":
            menu_search()
        elif choice == "2":
            menu_phones()
        elif choice == "3":
            menu_groups()
        elif choice == "4":
            menu_import_export()
        elif choice == "5":
            confirm = _ask("This will apply schema + procedures. Continue? [yes/no]: ",
                           choices=["yes", "no"])
            if confirm == "yes":
                init_db()


if __name__ == "__main__":
    main()