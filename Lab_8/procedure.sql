-- A procedure to insert a new user by name and phone; if the user already exists, update their phone
CREATE OR REPLACE PROCEDURE upsert_u(p_name VARCHAR, p_phone VARCHAR)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO phonebook (username, phone)
    VALUES (p_name, p_phone)
    ON CONFLICT (username) -- usually the primary key column
    DO UPDATE SET
        phone = EXCLUDED.phone;
END;
$$;

-- A procedure to insert many new users from a list of names and phones - use a loop and 
-- IF inside the procedure, validate phone correctness, and return all incorrect data
CREATE OR REPLACE PROCEDURE loophz(p_user VARCHAR[], p_phone VARCHAR[])
LANGUAGE plpgsql AS $$
BEGIN 
    FOR i IN 1..array_length(p_user, 1) LOOP
        IF p_phone[i] ~ '[a-zA-Z_!@#$%]' THEN 
            RAISE NOTICE 'Number % is invalid.', p_phone[i];
        ELSIF p_user[i] ~ '[0-9]' THEN
            RAISE NOTICE 'Name % is invalid.', p_user[i];
        ELSE
            CALL upsert_u(p_user[i], p_phone[i]);
        END IF;
    END LOOP;
END;
$$;

-- A procedure to delete data from the table by username or phone
CREATE OR REPLACE PROCEDURE del_user(p VARCHAR)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM phonebook 
    WHERE username = p OR phone = p;
END;
$$;