import subprocess
from io import BytesIO
from gtts import gTTS

def speak_text(text, speed=2):
    AUDIO_PLAYER_CMD = ["play", "-q", "-t", "mp3", "-", "tempo", "-s", str(speed)]
    with BytesIO() as mp3_fp:
        gTTS(text=text, lang="en").write_to_fp(mp3_fp)
        subprocess.run(AUDIO_PLAYER_CMD, input=mp3_fp.getvalue())