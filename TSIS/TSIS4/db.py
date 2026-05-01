# db.py — PostgreSQL persistence layer (psycopg2)
#
# Usage:
#   db = Database()
#   db.connect()
#   db.init_schema()
#   pid = db.get_or_create_player("Alice")
#   db.save_session(pid, score=120, level=4)
#   top10 = db.get_leaderboard()
#   best  = db.get_personal_best(pid)
#   db.close()

import psycopg2
import psycopg2.extras


# ── Connection defaults (override via environment or edit here) ────────────────
DEFAULT_DSN = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "postgres",
    "user":     "postgres",
    "password": "123456",
}

SQL_SCHEMA = """
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
"""


class Database:
    """Thin wrapper around a psycopg2 connection."""

    def __init__(self, dsn: dict | None = None):
        self._dsn  = dsn or DEFAULT_DSN
        self._conn = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Open the connection; return True on success, False on failure."""
        try:
            self._conn = psycopg2.connect(**self._dsn)
            self._conn.autocommit = False
            return True
        except psycopg2.OperationalError as exc:
            print(f"[DB] Connection failed: {exc}")
            self._conn = None
            return False

    def init_schema(self):
        """Create tables if they don't exist yet."""
        if not self._conn:
            return
        with self._conn.cursor() as cur:
            cur.execute(SQL_SCHEMA)
        self._conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def available(self) -> bool:
        return self._conn is not None

    # ── Players ───────────────────────────────────────────────────────────────

    def get_or_create_player(self, username: str) -> int | None:
        """Return the player's id, creating a row if needed."""
        if not self._conn:
            return None
        username = username.strip()[:50]
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO players (username) VALUES (%s) "
                    "ON CONFLICT (username) DO NOTHING",
                    (username,),
                )
                cur.execute(
                    "SELECT id FROM players WHERE username = %s",
                    (username,),
                )
                row = cur.fetchone()
            self._conn.commit()
            return row[0] if row else None
        except Exception as exc:
            print(f"[DB] get_or_create_player error: {exc}")
            self._conn.rollback()
            return None

    # ── Sessions ──────────────────────────────────────────────────────────────

    def save_session(self, player_id: int, score: int, level: int):
        """Persist a completed game session."""
        if not self._conn or player_id is None:
            return
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO game_sessions (player_id, score, level_reached) "
                    "VALUES (%s, %s, %s)",
                    (player_id, score, level),
                )
            self._conn.commit()
        except Exception as exc:
            print(f"[DB] save_session error: {exc}")
            self._conn.rollback()

    def get_leaderboard(self, limit: int = 10) -> list[dict]:
        """Return top-N rows sorted by score desc."""
        if not self._conn:
            return []
        try:
            with self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(
                    """
                    SELECT p.username,
                           gs.score,
                           gs.level_reached,
                           gs.played_at
                    FROM   game_sessions gs
                    JOIN   players       p ON p.id = gs.player_id
                    ORDER  BY gs.score DESC
                    LIMIT  %s
                    """,
                    (limit,),
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception as exc:
            print(f"[DB] get_leaderboard error: {exc}")
            return []

    def get_personal_best(self, player_id: int) -> int:
        """Return the player's highest score ever (0 if none)."""
        if not self._conn or player_id is None:
            return 0
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT COALESCE(MAX(score), 0) FROM game_sessions "
                    "WHERE player_id = %s",
                    (player_id,),
                )
                row = cur.fetchone()
            return row[0] if row else 0
        except Exception as exc:
            print(f"[DB] get_personal_best error: {exc}")
            return 0