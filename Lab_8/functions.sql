-- A function that returns all records matching a pattern (part of name, surname, or phone number)

CREATE OR REPLACE FUNCTION records(p text)
RETURNS TABLE(out_id INTEGER, out_name VARCHAR, out_phone VARCHAR) AS $$
BEGIN
    RETURN QUERY
        SELECT id, username, phone FROM phonebook 
        WHERE username ILIKE '%' || p || '%'
        OR phone ILIKE '%' || p || '%';
END;В
$$ LANGUAGE plpgsql;

-- A function that queries data from the table with pagination (by LIMIT and OFFSET)

CREATE OR REPLACE FUNCTION pagination(lim int, offs int)
RETURNS TABLE(out_id INTEGER, out_name VARCHAR, out_phone VARCHAR) AS $$
BEGIN
    RETURN QUERY
        SELECT id, username, phone
        FROM phonebook
        ORDER BY username
        LIMIT lim OFFSET offs;
END;
$$ LANGUAGE plpgsql;