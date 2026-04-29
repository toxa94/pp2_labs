import pygame

class MusicPlayer:
    def __init__(self, playlist):
        pygame.mixer.init()
        self.playlist = playlist
        self.current_index = 0
        self.is_playing = False
        self.is_paused = False
        self.start_time = 0
        self.pause_time = 0
        self.last_back_press = 0

    def play(self):
        pygame.mixer.music.load(self.playlist[self.current_index])
        pygame.mixer.music.play()
        self.start_time = pygame.time.get_ticks()
        self.is_playing = True
        self.is_paused = False

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False

    def pause_resume(self):
        if self.is_playing:
            if not self.is_paused:
                pygame.mixer.music.pause()
                self.pause_time = pygame.time.get_ticks()
                self.is_paused = True
            else:
                pygame.mixer.music.unpause()
                # уақытты түзетеміз
                self.start_time += pygame.time.get_ticks() - self.pause_time
                self.is_paused = False

    def next_track(self):
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play()

    def previous_track(self):
        current_time = pygame.time.get_ticks()

    # Егер 0.5 секунд ішінде қайта басылса → previous track
        if current_time - self.last_back_press < 500:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play()
        else:
        # Әйтпесе — тек restart
            self.play()

        self.last_back_press = current_time

    def get_current_track(self):
        return self.playlist[self.current_index]

    def get_position(self):
        if not self.is_playing or self.is_paused:
            return (self.pause_time - self.start_time) / 1000 if self.is_paused else 0
        return (pygame.time.get_ticks() - self.start_time) / 1000

    def get_length(self):
        sound = pygame.mixer.Sound(self.playlist[self.current_index])
        return sound.get_length()