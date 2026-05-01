-- schema.sql — Snake Game TSIS 4
-- Run once to initialize the database:
--   psql -U postgres -d snakegame -f schema.sql

CREATE TABLE IF NOT EXISTS players (
    id       SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS game_sessions (
    id            SERIAL PRIMARY KEY,
    player_id     INTEGER REFERENCES players(id) ON DELETE CASCADE,
    score         INTEGER   NOT NULL DEFAULT 0,
    level_reached INTEGER   NOT NULL DEFAULT 1,
    played_at     TIMESTAMP DEFAULT NOW()
);

-- Helpful index for leaderboard queries
CREATE INDEX IF NOT EXISTS idx_game_sessions_score
    ON game_sessions (score DESC);