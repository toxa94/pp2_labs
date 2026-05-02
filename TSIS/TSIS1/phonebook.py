import json
import csv
import os
from datetime import date, datetime
from connect import get_conn

PAGE_SIZE = 5

# Папка, где лежит сам скрипт — все файлы будем сохранять сюда
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ─────────────────────────────────────────────────────────────────────────────
# DB initialisation
# ─────────────────────────────────────────────────────────────────────────────
def init_db():
    conn = get_conn()
    base = os.path.dirname(os.path.abspath(__file__))
    for fname in ("sсhema.sql", "functions.sql", "procedures.sql"):
        path = os.path.join(base, fname)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                sql = f.read().strip()
            if sql:
                try:
                    conn.run(sql)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        print(f"  [SQL warning in {fname}] {e}")
        else:
            print(f"  [Warning] File {fname} not found!")
    conn.close()
    print("[DB] Schema and Logic ready.\n")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _fmt_date(d):
    return str(d) if d else "—"


def _print_table(rows, headers):
    if not rows:
        print("  (no results)")
        return
    col_w = [len(h) for h in headers]
    str_rows = []
    for r in rows:
        sr = [str(v) if v is not None else "—" for v in r]
        str_rows.append(sr)
        for i, v in enumerate(sr):
            col_w[i] = max(col_w[i], len(v))
    sep = "+" + "+".join("-" * (w + 2) for w in col_w) + "+"
    def row_line(cells):
        return "|" + "|".join(f" {c:<{col_w[i]}} " for i, c in enumerate(cells)) + "|"
    print(sep)
    print(row_line(headers))
    print(sep)
    for sr in str_rows:
        print(row_line(sr))
    print(sep)


def _get_groups(conn):
    rows = conn.run("SELECT id, name FROM groups ORDER BY name")
    return {r[1]: r[0] for r in rows}


def _get_or_create_group(conn, name):
    conn.run("INSERT INTO groups (name) VALUES (:n) ON CONFLICT (name) DO NOTHING", n=name)
    rows = conn.run("SELECT id FROM groups WHERE name = :n", n=name)
    return rows[0][0] if rows else None


# ─────────────────────────────────────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────────────────────────────────────
def add_contact():
    print("\n── Add Contact ──")
    name = input("Name: ").strip()
    if not name:
        print("Name cannot be empty."); return
    email    = input("Email (optional): ").strip() or None
    birthday = input("Birthday YYYY-MM-DD (optional): ").strip() or None

    conn = get_conn()
    groups = _get_groups(conn)
    print("Groups:", ", ".join(groups.keys()))
    grp_name = input("Group (leave blank for Other): ").strip() or "Other"
    group_id = _get_or_create_group(conn, grp_name)

    conn.run(
        "INSERT INTO contacts (name, email, birthday, group_id) "
        "VALUES (:n, :e, :b, :g)",
        n=name, e=email, b=birthday, g=group_id
    )
    rows = conn.run("SELECT id FROM contacts WHERE name=:n ORDER BY id DESC LIMIT 1", n=name)
    contact_id = rows[0][0]

    while True:
        phone = input("Phone number (leave blank to finish): ").strip()
        if not phone:
            break
        ptype = input("Type (home/work/mobile) [mobile]: ").strip() or "mobile"
        if ptype not in ("home", "work", "mobile"):
            ptype = "mobile"
        conn.run(
            "INSERT INTO phones (contact_id, phone, type) VALUES (:c, :p, :t)",
            c=contact_id, p=phone, t=ptype
        )

    conn.close()
    print(f"  Contact '{name}' added.")


def view_all(sort_by="name"):
    conn = get_conn()
    rows = conn.run(f"""
        SELECT c.name, c.email, c.birthday, g.name,
               STRING_AGG(ph.phone || ' (' || COALESCE(ph.type,'?') || ')', ', ')
        FROM contacts c
        LEFT JOIN groups g  ON g.id = c.group_id
        LEFT JOIN phones ph ON ph.contact_id = c.id
        GROUP BY c.id, c.name, c.email, c.birthday, g.name, c.created_at
        ORDER BY c.{sort_by} ASC NULLS LAST
    """)
    conn.close()
    print()
    _print_table(rows, ["Name", "Email", "Birthday", "Group", "Phones"])


def search_contact():
    query = input("Search (name / email / phone): ").strip()
    conn  = get_conn()
    rows  = conn.run(
        "SELECT * FROM search_contacts(:q)", q=query
    )
    conn.close()
    _print_table(rows, ["ID", "Name", "Email", "Birthday", "Group", "Phones"])


def update_contact():
    print("\n── Update Contact ──")
    name = input("Contact name to update: ").strip()
    conn = get_conn()
    rows = conn.run("SELECT id, name, email, birthday FROM contacts WHERE name ILIKE :n", n=name)
    if not rows:
        print("  Not found."); conn.close(); return
    cid, cname, cemail, cbday = rows[0]
    print(f"  Found: {cname} | {cemail} | {cbday}")

    new_email = input(f"New email [{cemail}]: ").strip() or cemail
    new_bday  = input(f"New birthday [{cbday}]: ").strip() or cbday

    conn.run(
        "UPDATE contacts SET email=:e, birthday=:b WHERE id=:i",
        e=new_email, b=new_bday or None, i=cid
    )
    conn.close()
    print("  Updated.")


def delete_contact():
    name = input("Contact name to delete: ").strip()
    conn = get_conn()
    rows = conn.run("SELECT id FROM contacts WHERE name ILIKE :n", n=name)
    if not rows:
        print("  Not found."); conn.close(); return
    confirm = input(f"  Delete '{name}'? (y/n): ").strip().lower()
    if confirm == "y":
        conn.run("DELETE FROM contacts WHERE id = :i", i=rows[0][0])
        print("  Deleted.")
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Filter & sort
# ─────────────────────────────────────────────────────────────────────────────
def filter_by_group():
    conn   = get_conn()
    groups = _get_groups(conn)
    print("Available groups:", ", ".join(groups.keys()))
    grp = input("Group name: ").strip()
    if grp not in groups:
        print("  Group not found."); conn.close(); return
    rows = conn.run("""
        SELECT c.name, c.email, c.birthday,
               STRING_AGG(ph.phone || ' (' || COALESCE(ph.type,'?') || ')', ', ')
        FROM contacts c
        LEFT JOIN phones ph ON ph.contact_id = c.id
        WHERE c.group_id = :g
        GROUP BY c.id, c.name, c.email, c.birthday
        ORDER BY c.name
    """, g=groups[grp])
    conn.close()
    _print_table(rows, ["Name", "Email", "Birthday", "Phones"])


def search_by_email():
    query = input("Email pattern (e.g. gmail): ").strip()
    conn  = get_conn()
    rows  = conn.run("""
        SELECT c.name, c.email, c.birthday, g.name
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        WHERE c.email ILIKE :q
        ORDER BY c.name
    """, q=f"%{query}%")
    conn.close()
    _print_table(rows, ["Name", "Email", "Birthday", "Group"])


def sort_and_view():
    print("Sort by: 1) name  2) birthday  3) created_at")
    choice = input("Choice [1]: ").strip()
    sort_map = {"1": "name", "2": "birthday", "3": "created_at"}
    sort_by  = sort_map.get(choice, "name")
    view_all(sort_by)


# ─────────────────────────────────────────────────────────────────────────────
# Paginated navigation
# ─────────────────────────────────────────────────────────────────────────────
def paginated_browse():
    print("Sort by: 1) name  2) birthday  3) created_at")
    choice  = input("Choice [1]: ").strip()
    sort_map = {"1": "name", "2": "birthday", "3": "created_at"}
    sort_by  = sort_map.get(choice, "name")

    page = 0
    while True:
        conn = get_conn()
        rows = conn.run(
            "SELECT * FROM paginated_contacts(:lim, :off, :s)",
            lim=PAGE_SIZE, off=page * PAGE_SIZE, s=sort_by
        )
        conn.close()

        print(f"\n── Page {page + 1} ──")
        _print_table(rows, ["ID", "Name", "Email", "Birthday", "Group", "Phones"])

        nav = input("  [n]ext / [p]rev / [q]uit: ").strip().lower()
        if nav == "n":
            if len(rows) < PAGE_SIZE:
                print("  Last page.")
            else:
                page += 1
        elif nav == "p":
            page = max(0, page - 1)
        elif nav == "q":
            break


# ─────────────────────────────────────────────────────────────────────────────
# Phone management
# ─────────────────────────────────────────────────────────────────────────────
def add_phone_menu():
    name  = input("Contact name: ").strip()
    phone = input("Phone number: ").strip()
    ptype = input("Type (home/work/mobile) [mobile]: ").strip() or "mobile"
    conn  = get_conn()
    try:
        conn.run("CALL add_phone(:n, :p, :t)", n=name, p=phone, t=ptype)
        print("  Phone added.")
    except Exception as e:
        print(f"  Error: {e}")
    conn.close()


def move_to_group_menu():
    name  = input("Contact name: ").strip()
    group = input("Target group: ").strip()
    conn  = get_conn()
    try:
        conn.run("CALL move_to_group(:n, :g)", n=name, g=group)
        print("  Moved.")
    except Exception as e:
        print(f"  Error: {e}")
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Import / Export
# ─────────────────────────────────────────────────────────────────────────────
def export_json():
    default_name = "contacts.json"
    fname = input(f"Output filename [{default_name}]: ").strip() or default_name

    # Если пользователь не указал полный путь — сохраняем рядом со скриптом
    if not os.path.isabs(fname):
        fname = os.path.join(BASE_DIR, fname)

    conn = get_conn()
    rows = conn.run("""
        SELECT c.id, c.name, c.email, c.birthday::TEXT, g.name AS grp
        FROM contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        ORDER BY c.name
    """)
    data = []
    for cid, name, email, bday, grp in rows:
        phones = conn.run(
            "SELECT phone, type FROM phones WHERE contact_id = :i", i=cid
        )
        data.append({
            "name":     name,
            "email":    email,
            "birthday": bday,
            "group":    grp,
            "phones":   [{"phone": p, "type": t} for p, t in phones],
        })
    conn.close()

    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  Exported {len(data)} contacts to:")
    print(f"  {fname}")


def import_json():
    default_name = "contacts.json"
    fname = input(f"JSON filename [{default_name}]: ").strip() or default_name

    # Если путь относительный — ищем рядом со скриптом
    if not os.path.isabs(fname):
        fname = os.path.join(BASE_DIR, fname)

    if not os.path.exists(fname):
        print(f"  File '{fname}' not found."); return

    with open(fname, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = get_conn()
    inserted = skipped = overwritten = 0

    for item in data:
        name = item.get("name", "").strip()
        if not name:
            continue
        existing = conn.run("SELECT id FROM contacts WHERE name = :n", n=name)

        if existing:
            choice = input(f"  '{name}' already exists. [s]kip / [o]verwrite? ").strip().lower()
            if choice != "o":
                skipped += 1
                continue
            cid = existing[0][0]
            conn.run(
                "UPDATE contacts SET email=:e, birthday=:b WHERE id=:i",
                e=item.get("email"), b=item.get("birthday"), i=cid
            )
            conn.run("DELETE FROM phones WHERE contact_id = :i", i=cid)
            overwritten += 1
        else:
            group_id = _get_or_create_group(conn, item.get("group") or "Other")
            conn.run(
                "INSERT INTO contacts (name, email, birthday, group_id) "
                "VALUES (:n, :e, :b, :g)",
                n=name, e=item.get("email"), b=item.get("birthday"), g=group_id
            )
            rows = conn.run(
                "SELECT id FROM contacts WHERE name=:n ORDER BY id DESC LIMIT 1", n=name
            )
            cid = rows[0][0]
            inserted += 1

        for ph in item.get("phones", []):
            conn.run(
                "INSERT INTO phones (contact_id, phone, type) VALUES (:c, :p, :t)",
                c=cid, p=ph.get("phone"), t=ph.get("type", "mobile")
            )

    conn.close()
    print(f"  Done: {inserted} inserted, {overwritten} overwritten, {skipped} skipped.")


def import_csv():
    default_name = "contacts.csv"
    fname = input(f"CSV filename [{default_name}]: ").strip() or default_name

    # Если путь относительный — ищем рядом со скриптом
    if not os.path.isabs(fname):
        fname = os.path.join(BASE_DIR, fname)

    if not os.path.exists(fname):
        print(f"  File '{fname}' not found."); return

    conn = get_conn()
    inserted = skipped = 0

    with open(fname, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter='\t')
        contacts_map = {}
        for row in reader:
            name = row.get("name", "").strip()
            if not name:
                continue
            if name not in contacts_map:
                contacts_map[name] = {
                    "email":    row.get("email", "").strip() or None,
                    "birthday": row.get("birthday", "").strip() or None,
                    "group":    row.get("group", "Other").strip() or "Other",
                    "phones":   [],
                }
            phone = row.get("phone", "").strip()
            ptype = row.get("phone_type", "mobile").strip() or "mobile"
            if phone:
                contacts_map[name]["phones"].append({"phone": phone, "type": ptype})

    for name, item in contacts_map.items():
        existing = conn.run("SELECT id FROM contacts WHERE name = :n", n=name)
        if existing:
            skipped += 1
            continue
        group_id = _get_or_create_group(conn, item["group"])
        conn.run(
            "INSERT INTO contacts (name, email, birthday, group_id) "
            "VALUES (:n, :e, :b, :g)",
            n=name, e=item["email"], b=item["birthday"], g=group_id
        )
        rows = conn.run(
            "SELECT id FROM contacts WHERE name=:n ORDER BY id DESC LIMIT 1", n=name
        )
        cid = rows[0][0]
        for ph in item["phones"]:
            conn.run(
                "INSERT INTO phones (contact_id, phone, type) VALUES (:c, :p, :t)",
                c=cid, p=ph["phone"], t=ph["type"]
            )
        inserted += 1

    conn.close()
    print(f"  CSV import done: {inserted} inserted, {skipped} skipped (already exist).")


# ─────────────────────────────────────────────────────────────────────────────
# Main menu
# ─────────────────────────────────────────────────────────────────────────────
MENU = """
╔══════════════════════════════════════╗
║         PhoneBook — TSIS 1           ║
╠══════════════════════════════════════╣
║  1. Add contact                      ║
║  2. View all contacts                ║
║  3. Search (name / email / phone)    ║
║  4. Update contact                   ║
║  5. Delete contact                   ║
║──────────────────────────────────────║
║  6. Filter by group                  ║
║  7. Search by email                  ║
║  8. Sort & view                      ║
║  9. Browse with pagination           ║
║──────────────────────────────────────║
║ 10. Add phone to contact             ║
║ 11. Move contact to group            ║
║──────────────────────────────────────║
║ 12. Export to JSON                   ║
║ 13. Import from JSON                 ║
║ 14. Import from CSV                  ║
║──────────────────────────────────────║
║  0. Exit                             ║
╚══════════════════════════════════════╝
"""

ACTIONS = {
    "1":  add_contact,
    "2":  view_all,
    "3":  search_contact,
    "4":  update_contact,
    "5":  delete_contact,
    "6":  filter_by_group,
    "7":  search_by_email,
    "8":  sort_and_view,
    "9":  paginated_browse,
    "10": add_phone_menu,
    "11": move_to_group_menu,
    "12": export_json,
    "13": import_json,
    "14": import_csv,
}


def main():
    print("Initialising database...")
    init_db()

    while True:
        print(MENU)
        choice = input("Choice: ").strip()
        if choice == "0":
            print("Bye!"); break
        action = ACTIONS.get(choice)
        if action:
            try:
                action()
            except Exception as e:
                print(f"  [Error] {e}")
        else:
            print("  Unknown option.")


if __name__ == "__main__":
    main()