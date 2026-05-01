-- schema.sql — Extended PhoneBook schema

-- ─────────────────────────────────────────────
-- 0. Base contacts table (from Practice 7)
--    Created here if it doesn't exist yet
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contacts (
    id    SERIAL PRIMARY KEY,
    name  VARCHAR(100) NOT NULL,
    phone VARCHAR(20)
);

-- ─────────────────────────────────────────────
-- 1. Groups lookup table
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS groups (
    id   SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

-- Seed the four standard groups
INSERT INTO groups (name) VALUES
    ('Family'), ('Work'), ('Friend'), ('Other')
ON CONFLICT (name) DO NOTHING;


-- ─────────────────────────────────────────────
-- 2. Extend contacts with new columns
-- ─────────────────────────────────────────────
ALTER TABLE contacts
    ADD COLUMN IF NOT EXISTS email      VARCHAR(100),
    ADD COLUMN IF NOT EXISTS birthday   DATE,
    ADD COLUMN IF NOT EXISTS group_id   INTEGER REFERENCES groups(id),
    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();


-- ─────────────────────────────────────────────
-- 3. Phones table (1-to-many with contacts)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS phones (
    id         SERIAL PRIMARY KEY,
    contact_id INTEGER     NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    phone      VARCHAR(20) NOT NULL,
    type       VARCHAR(10) NOT NULL DEFAULT 'mobile'
                           CHECK (type IN ('home', 'work', 'mobile'))
);

CREATE INDEX IF NOT EXISTS idx_phones_contact_id ON phones(contact_id);