# speaker.py — Nyro v4 — TTS + Arduino Mouth Animation
# Nyro model → Piper TTS (offline, Hindi female)
# Bhai model → Edge TTS (online, Hindi male casual)
# Sends START_SPEECH / frame numbers / END_SPEECH to Arduino
# -*- coding: utf-8 -*-
import subprocess, threading, time
import servo_ctrl
from config import (
    TTS_NYRO_ENGINE, TTS_BHAI_ENGINE,
    PIPER_BIN, PIPER_MODEL, EDGE_VOICE_BHAI,
    AUDIO_WAV, AUDIO_MP3
)

_player       = None
_stop_flag    = threading.Event()
speaking_lock = threading.Lock()

# ── Arduino serial write ──────────────────────────────────────
def _ard(cmd: bytes):
    try:
        from arduino_ctrl import write
        write(cmd)
    except: pass

# ════════════════════════════════════════════════════════════
#  MOUTH PATTERNS — context-aware
# ════════════════════════════════════════════════════════════
_PATTERNS = {
    "excited":  [0,4,5,4,3,5,1,3],
    "question": [2,3,4,3,2,3,2],
    "soft":     [1,2,1,2,1,2],
    "normal":   [1,3,2,4,2,3,1],
}

def _mouth_pattern(text: str):
    t = text.lower()
    if any(w in t for w in ["!", "waah", "arre", "mast", "yaar", "chal"]):
        return _PATTERNS["excited"]
    if t.strip().endswith("?"):
        return _PATTERNS["question"]
    if any(w in t for w in ["udaas", "sorry", "theek", "dukhi"]):
        return _PATTERNS["soft"]
    return _PATTERNS["normal"]

# ════════════════════════════════════════════════════════════
#  TTS ENGINES
# ════════════════════════════════════════════════════════════

def _piper(text: str) -> bool:
    """Offline Hindi female — best for Nyro."""
    try:
        r = subprocess.run(
            [PIPER_BIN, "--model", PIPER_MODEL,
             "--output_file", AUDIO_WAV, "--quiet"],
            input=text.encode("utf-8"),
            capture_output=True, timeout=12
        )
        return r.returncode == 0
    except Exception as e:
        print(f"[Speaker] Piper error: {e}")
        return False

def _edge(text: str, voice: str) -> bool:
    """Edge TTS — natural male voice for Bhai."""
    try:
        import asyncio, edge_tts
        async def _run():
            await edge_tts.Communicate(text, voice).save(AUDIO_MP3)
        asyncio.run(_run())
        return True
    except Exception as e:
        print(f"[Speaker] Edge error: {e}")
        return False

def _gtts_fallback(text: str) -> bool:
    try:
        from gtts import gTTS
        gTTS(text=text, lang="hi").save(AUDIO_MP3)
        return True
    except: return False

def _generate(text: str, mode: str):
    """Returns (filepath, is_wav)"""
    if mode == "nyro":
        if _piper(text): return AUDIO_WAV, True
        if _edge(text, EDGE_VOICE_BHAI): return AUDIO_MP3, False   # fallback
    else:  # bhai
        if _edge(text, EDGE_VOICE_BHAI): return AUDIO_MP3, False
        if _piper(text): return AUDIO_WAV, True   # fallback
    if _gtts_fallback(text): return AUDIO_MP3, False
    return None, False

# ════════════════════════════════════════════════════════════
#  MAIN SPEAK FUNCTION
# ════════════════════════════════════════════════════════════

def speak(text: str, mode: str = "nyro"):
    global _player
    _stop_flag.clear()

    with speaking_lock:
        # Servo gesture before speaking
        gesture = servo_ctrl.gesture_for(text, mode)
        if gesture:
            gesture()
            time.sleep(0.25)

        audio_path, is_wav = _generate(text, mode)
        if not audio_path:
            print("[Speaker] No audio generated.")
            return

        cmd = ["aplay", "-q", audio_path] if is_wav else ["mpg123", "-q", audio_path]

        _ard(b'START_SPEECH\n')
        _player = subprocess.Popen(cmd)

        frames = _mouth_pattern(text)
        idx = 0

        while True:
            if _stop_flag.is_set(): break
            if _player.poll() is not None: break
            frame = frames[idx % len(frames)]
            _ard(f"{frame}\n".encode())
            idx += 1
            time.sleep(0.10)

        _kill()
        _ard(b'END_SPEECH\n')
        servo_ctrl.idle()

def stop():
    _stop_flag.set()
    _kill()
    _ard(b'END_SPEECH\n')

def _kill():
    global _player
    try:
        if _player and _player.poll() is None:
            _player.terminate()
            time.sleep(0.05)
            if _player.poll() is None:
                _player.kill()
    except: pass
    _player = None
