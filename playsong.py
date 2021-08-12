import signal
import subprocess
import threading
import time


class PlaySong(threading.Thread):
    _SLEEP_DURATION = 0.1 # this is the number of seconds to sleep before re-checking conditions

    def __init__(self, pi_player, file_name):
        super().__init__(target=self._begin_playing_song, args=[file_name])
        self._user_play_pause = threading.Event()
        self._user_stop = threading.Event()
        self._is_song_playing = True
        self._song_player_proc = None
        self.pi_player = pi_player

    def _begin_playing_song(self, file_name):
        SONG_PLAYER_CMD = ["play", '-q', file_name, '-t', 'alsa']
        self._song_player_proc = subprocess.Popen(SONG_PLAYER_CMD)
        while True:
            # if the user hit stop, terminate the subprocess then return
            if self._is_user_stopped():
                self._song_player_proc.terminate()
                return
            # if the user hit play/pause, send either SIGSTOP or SIGCONT
            elif self._is_user_played_paused():
                self._song_player_proc.send_signal(signal.SIGSTOP) if self._is_song_playing else self._song_player_proc.send_signal(signal.SIGCONT)
                self._is_song_playing = not self._is_song_playing
                self._clear_user_play_pause()
            # if subprocess completed, call piplayer.next then return
            elif self._song_player_proc.poll() is not None:
                self.pi_player.play_next_song()
                return
            # otherwise, sleep for small amount of time then repeat
            else:
                time.sleep(PlaySong._SLEEP_DURATION)

    def user_stop(self):
        self._user_stop.set()

    def user_play_pause(self):
        self._user_play_pause.set()

    def _is_user_stopped(self):
        return self._user_stop.is_set()

    def _is_user_played_paused(self):
        return self._user_play_pause.is_set()

    def _clear_user_play_pause(self):
        self._user_play_pause.clear()
