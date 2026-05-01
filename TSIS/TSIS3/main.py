"""
main.py
Entry point for the Racer game.
Manages the top-level state machine:
  main_menu → username_entry → playing → game_over
                             ↘ leaderboard
                             ↘ settings
"""

import pygame
import sys
import os

# Ensure we run from the TSIS3 directory so assets/ paths resolve
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from racer       import GameSession, SCREEN_W, SCREEN_H, FPS
from ui          import MainMenu, UsernameEntry, SettingsScreen, LeaderboardScreen, GameOverScreen
from persistence import load_settings, save_settings, load_leaderboard, save_score


# ─── Sound Manager ────────────────────────────────────────────────────────────

class SoundManager:
    """Loads and plays sound effects; respects the mute setting."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._sounds: dict = {}
        self._load()

    def _load(self) -> None:
        clips = {
            "coin":  "assets/getcoin.mp3",
            "crash": "assets/crash.wav",
        }
        for name, path in clips.items():
            try:
                self._sounds[name] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"[sound] Could not load {path}: {e}")

    def play(self, name: str) -> None:
        if self.enabled and name in self._sounds:
            self._sounds[name].play()

    def set_enabled(self, val: bool) -> None:
        self.enabled = val


# ─── Main game loop ───────────────────────────────────────────────────────────

def main() -> None:
    pygame.init()
    pygame.mixer.init()

    screen  = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("RACER — Advanced Edition")
    clock   = pygame.time.Clock()

    # Load persisted data
    settings    = load_settings()
    sound       = SoundManager(settings.get("sound", True))

    # State machine
    # States: "main_menu" | "username" | "playing" | "game_over" | "leaderboard" | "settings"
    state       = "main_menu"
    username    = "Player"

    # Screen objects (created lazily / on-demand)
    main_menu   = MainMenu()
    username_screen: UsernameEntry | None          = None
    settings_screen: SettingsScreen | None         = None
    leaderboard_screen: LeaderboardScreen | None   = None
    game_over_screen: GameOverScreen | None        = None
    session: GameSession | None                    = None

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0   # seconds since last frame

        # ── Events ────────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Dispatch events to active screen / session
            if state == "main_menu":
                action = main_menu.handle_event(event)
                if action == "play":
                    username_screen = UsernameEntry()
                    state = "username"
                elif action == "leaderboard":
                    leaderboard_screen = LeaderboardScreen(load_leaderboard())
                    state = "leaderboard"
                elif action == "settings":
                    settings_screen = SettingsScreen(settings)
                    state = "settings"
                elif action == "quit":
                    running = False

            elif state == "username":
                result = username_screen.handle_event(event)
                if result:
                    action, value = result
                    if action == "start":
                        username = value
                        session  = GameSession(settings, sound)
                        state    = "playing"
                    elif action == "back":
                        state = "main_menu"

            elif state == "playing":
                if session:
                    session.handle_event(event)
                # ESC pauses / returns to menu
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = "main_menu"

            elif state == "game_over":
                if game_over_screen:
                    action = game_over_screen.handle_event(event)
                    if action == "retry":
                        session  = GameSession(settings, sound)
                        state    = "playing"
                    elif action == "menu":
                        state = "main_menu"

            elif state == "leaderboard":
                if leaderboard_screen:
                    action = leaderboard_screen.handle_event(event)
                    if action == "back":
                        state = "main_menu"

            elif state == "settings":
                if settings_screen:
                    action = settings_screen.handle_event(event)
                    if action == "save":
                        settings = settings_screen.settings
                        save_settings(settings)
                        sound.set_enabled(settings.get("sound", True))
                        state = "main_menu"
                    elif action == "back":
                        state = "main_menu"

        # ── Update ────────────────────────────────────────────────────────────
        if state == "main_menu":
            main_menu.update(dt)

        elif state == "username" and username_screen:
            username_screen.update(dt)

        elif state == "playing" and session:
            session.update(dt)
            # Check for game over
            if session.game_over:
                dist_m = int(session.distance // 10)
                save_score(username, session.score, dist_m, session.coin_count)
                game_over_screen = GameOverScreen(session.score, dist_m, session.coin_count)
                state = "game_over"

        elif state == "game_over" and game_over_screen:
            game_over_screen.update(dt)

        elif state == "leaderboard" and leaderboard_screen:
            leaderboard_screen.update(dt)

        elif state == "settings" and settings_screen:
            settings_screen.update(dt)

        # ── Draw ──────────────────────────────────────────────────────────────
        if state == "main_menu":
            main_menu.draw(screen)

        elif state == "username" and username_screen:
            username_screen.draw(screen)

        elif state == "playing" and session:
            session.draw(screen)

        elif state == "game_over" and game_over_screen:
            game_over_screen.draw(screen)

        elif state == "leaderboard" and leaderboard_screen:
            leaderboard_screen.draw(screen)

        elif state == "settings" and settings_screen:
            settings_screen.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()