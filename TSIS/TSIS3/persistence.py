"""
persistence.py
Handles loading and saving of leaderboard and settings data to JSON files.
"""

import json
import os

LEADERBOARD_FILE = "leaderboard.json"
SETTINGS_FILE = "settings.json"

# ─── Default values ────────────────────────────────────────────────────────────

DEFAULT_SETTINGS = {
    "sound": True,
    "car_color": "blue",    # blue | red | green | yellow
    "difficulty": "normal"  # easy | normal | hard
}


# ─── Settings ──────────────────────────────────────────────────────────────────

def load_settings() -> dict:
    """Load settings from file, filling in defaults for missing keys."""
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
        # Merge with defaults so new keys are always present
        merged = DEFAULT_SETTINGS.copy()
        merged.update(data)
        return merged
    except (json.JSONDecodeError, IOError):
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    """Persist settings dict to disk."""
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except IOError as e:
        print(f"[persistence] Could not save settings: {e}")


# ─── Leaderboard ───────────────────────────────────────────────────────────────

def load_leaderboard() -> list:
    """Return the stored leaderboard list (up to 10 entries)."""
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, IOError):
        return []


def save_score(username: str, score: int, distance: int, coins: int) -> None:
    """
    Append a new score entry and keep only the top 10 sorted by score.
    Each entry: {"username", "score", "distance", "coins"}
    """
    board = load_leaderboard()
    board.append({
        "username": username,
        "score": score,
        "distance": distance,
        "coins": coins
    })
    # Sort descending by score, keep top 10
    board.sort(key=lambda e: e["score"], reverse=True)
    board = board[:10]
    try:
        with open(LEADERBOARD_FILE, "w") as f:
            json.dump(board, f, indent=2)
    except IOError as e:
        print(f"[persistence] Could not save leaderboard: {e}")