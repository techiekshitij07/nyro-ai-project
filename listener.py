# listener.py — Nyro v3 Microphone Listener
# -*- coding: utf-8 -*-
import queue, threading
import speech_recognition as sr
from config import LANG_RECOG, STOP_WORDS, MODE_TRIGGERS

_q         = queue.Queue()
_stop_cb   = None          # speaker.stop reference (main.py set karega)
_mode_cb   = None          # mode change callback (main.py set karega)

r   = sr.Recognizer()
r.energy_threshold       = 300
r.dynamic_energy_threshold = True
mic = sr.Microphone()

# ── Calibrate mic once ───────────────────────────────────────
print("[Listener] Mic calibrate ho raha hai...")
with mic as source:
    r.adjust_for_ambient_noise(source, duration=1)
print("[Listener] Ready.")

# ════════════════════════════════════════════════════════════
#  BACKGROUND CALLBACK
# ════════════════════════════════════════════════════════════

def _callback(recognizer, audio):
    try:
        text = recognizer.recognize_google(audio, language=LANG_RECOG).strip()
        if not text:
            return
        print(f"[Listener] HEARD: {text}")
        low = text.lower()

        # Stop command
        if any(w in low for w in STOP_WORDS):
            if _stop_cb:
                _stop_cb()
            return

        # Mode switch command
        for trigger, mode in MODE_TRIGGERS.items():
            if trigger in low:
                if _mode_cb:
                    _mode_cb(mode)
                print(f"[Listener] Mode switch → {mode}")
                return

        _q.put(text)

    except sr.UnknownValueError:
        pass   # Samjha nahi — quiet skip
    except Exception as e:
        print(f"[Listener] ERR: {e}")

# ════════════════════════════════════════════════════════════
#  PUBLIC API
# ════════════════════════════════════════════════════════════

def start(stop_callback=None, mode_callback=None):
    """Background listening shuru karo."""
    global _stop_cb, _mode_cb, _stop_listen
    _stop_cb  = stop_callback
    _mode_cb  = mode_callback
    _stop_listen = r.listen_in_background(mic, _callback, phrase_time_limit=5)
    print("[Listener] Background listening started.")

def stop():
    if _stop_listen:
        _stop_listen(wait_for_stop=False)

def get(timeout=0.5):
    """Queue se next heard text lo. None agar kuch nahi."""
    try:
        return _q.get(timeout=timeout)
    except queue.Empty:
        return None
