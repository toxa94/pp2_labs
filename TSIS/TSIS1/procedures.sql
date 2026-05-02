CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE name ILIKE p_contact_name
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found', p_contact_name;
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type);

    RAISE NOTICE 'Phone % (%) added to contact "%"', p_phone, p_type, p_contact_name;
END;
$$;


-- ─────────────────────────────────────────────────────────────────────────────
-- 2. move_to_group — move contact to a group, create group if needed
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
    v_group_id   INTEGER;
BEGIN
    -- Get or create group
    INSERT INTO groups (name) VALUES (p_group_name)
    ON CONFLICT (name) DO NOTHING;

    SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;

    -- Find contact
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE name ILIKE p_contact_name
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found', p_contact_name;
    END IF;

    UPDATE contacts SET group_id = v_group_id WHERE id = v_contact_id;

    RAISE NOTICE 'Contact "%" moved to group "%"', p_contact_name, p_group_name;
END;
$$;


-- ─────────────────────────────────────────────────────────────────────────────
-- 3. search_contacts — search across name, email, and all phones
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE (
    id       INTEGER,
    name     VARCHAR,
    email    VARCHAR,
    birthday DATE,
    grp      VARCHAR,
    phones   TEXT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        c.id,
        c.name,
        c.email,
        c.birthday,
        g.name   AS grp,
        STRING_AGG(p.phone || ' (' || COALESCE(p.type, '?') || ')', ', ')
            OVER (PARTITION BY c.id) AS phones
    FROM contacts c
    LEFT JOIN groups g ON g.id = c.group_id
    LEFT JOIN phones p ON p.contact_id = c.id
    WHERE
        c.name  ILIKE '%' || p_query || '%' OR
        c.email ILIKE '%' || p_query || '%' OR
        p.phone ILIKE '%' || p_query || '%'
    ORDER BY c.name;
END;
$$;


-- ─────────────────────────────────────────────────────────────────────────────
-- 4. paginated_contacts — list contacts with LIMIT/OFFSET
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION paginated_contacts(
    p_limit  INTEGER DEFAULT 10,
    p_offset INTEGER DEFAULT 0,
    p_sort   VARCHAR DEFAULT 'name'   -- 'name' | 'birthday' | 'created_at'
)
RETURNS TABLE (
    id       INTEGER,
    name     VARCHAR,
    email    VARCHAR,
    birthday DATE,
    grp      VARCHAR,
    phones   TEXT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.name,
        c.email,
        c.birthday,
        g.name AS grp,
        STRING_AGG(ph.phone || ' (' || COALESCE(ph.type,'?') || ')', ', ') AS phones
    FROM contacts c
    LEFT JOIN groups g  ON g.id  = c.group_id
    LEFT JOIN phones ph ON ph.contact_id = c.id
    GROUP BY c.id, c.name, c.email, c.birthday, g.name, c.created_at
    ORDER BY
        CASE WHEN p_sort = 'birthday'   THEN c.birthday::TEXT    END ASC NULLS LAST,
        CASE WHEN p_sort = 'created_at' THEN c.created_at::TEXT  END ASC NULLS LAST,
        CASE WHEN p_sort = 'name'       THEN c.name              END ASC NULLS LAST
    LIMIT  p_limit
    OFFSET p_offset;
END;
$$;