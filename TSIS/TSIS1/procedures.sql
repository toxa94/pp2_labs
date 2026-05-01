-- procedures.sql — New PL/pgSQL objects for TSIS1
-- (Does NOT duplicate procedures from Practice 8)

-- ─────────────────────────────────────────────
-- 1. add_phone — attach a phone number to a contact
-- ─────────────────────────────────────────────
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR DEFAULT 'mobile'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    -- Resolve contact by name (case-insensitive)
    SELECT id INTO v_contact_id
    FROM   contacts
    WHERE  LOWER(name) = LOWER(p_contact_name)
    LIMIT  1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found', p_contact_name;
    END IF;

    -- Validate phone type
    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Invalid phone type "%". Use: home, work, mobile', p_type;
    END IF;

    -- Insert the new phone number
    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type);

    RAISE NOTICE 'Phone % (%) added to contact "%"', p_phone, p_type, p_contact_name;
END;
$$;


-- ─────────────────────────────────────────────
-- 2. move_to_group — reassign contact's group
--    Creates the group automatically if missing
-- ─────────────────────────────────────────────
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
    v_group_id   INTEGER;
BEGIN
    -- Resolve contact
    SELECT id INTO v_contact_id
    FROM   contacts
    WHERE  LOWER(name) = LOWER(p_contact_name)
    LIMIT  1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found', p_contact_name;
    END IF;

    -- Find or create the group
    SELECT id INTO v_group_id
    FROM   groups
    WHERE  LOWER(name) = LOWER(p_group_name);

    IF v_group_id IS NULL THEN
        INSERT INTO groups (name) VALUES (p_group_name)
        RETURNING id INTO v_group_id;
        RAISE NOTICE 'Group "%" created', p_group_name;
    END IF;

    -- Update the contact
    UPDATE contacts
    SET    group_id = v_group_id
    WHERE  id = v_contact_id;

    RAISE NOTICE 'Contact "%" moved to group "%"', p_contact_name, p_group_name;
END;
$$;


-- ─────────────────────────────────────────────
-- 3. search_contacts — full-field search
--    Matches: name, email, and ALL phone numbers
-- ─────────────────────────────────────────────
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE (
    id         INTEGER,
    name       VARCHAR,
    email      VARCHAR,
    birthday   DATE,
    group_name VARCHAR,
    phones     TEXT        -- comma-separated list of phone numbers
)
LANGUAGE plpgsql AS $$
DECLARE
    v_pattern TEXT := '%' || LOWER(p_query) || '%';
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.name,
        c.email,
        c.birthday,
        g.name                                     AS group_name,
        STRING_AGG(p.phone || ' (' || p.type || ')', ', ') AS phones
    FROM  contacts c
    LEFT  JOIN groups g ON g.id = c.group_id
    LEFT  JOIN phones p ON p.contact_id = c.id
    WHERE
        LOWER(c.name)  LIKE v_pattern  OR
        LOWER(c.email) LIKE v_pattern  OR
        p.phone        LIKE v_pattern          -- match any associated phone
    GROUP BY c.id, c.name, c.email, c.birthday, g.name
    ORDER BY c.name;
END;
$$;