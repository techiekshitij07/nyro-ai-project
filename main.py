# main.py — Nyro v4 Final — Lag-Free Entry Point
# -*- coding: utf-8 -*-
"""
Nyro v4 — Dual Model AI Robot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Chalao:  bash start_nyro.sh
         ya: source venv/bin/activate && python3 main.py

Voice commands:
  "switch nyro" / "hello nyro"  → Model 1 (serious face)
  "switch bhai"                  → Model 2 (fun face + games)
  "game khelo"                   → Number guessing game (Bhai mode)
  "game band"                    → Game stop, Bhai face wapas
  "temperature" / "tapman"       → Live DHT11 reading
  "stop nyro"                    → Baat rokna
  Ctrl+C                         → Band karna

Architecture (lag-free — 3 threads):
  Thread 1: Listener (always on, never blocks)
  Thread 2: Brain worker (Gemini API call async)
  Thread 3: Speaker worker (TTS + Arduino)
"""

import time, threading, queue as _q
import listener, speaker, brain, memory
import sensor_ctrl, servo_ctrl, arduino_ctrl
from config import DEFAULT_MODE, TRIGGER_NYRO, TRIGGER_BHAI

# ── Global state ──────────────────────────────────────────────
current_mode  = DEFAULT_MODE
_mode_lock    = threading.Lock()
_brain_q      = _q.Queue()
_reply_q      = _q.Queue(maxsize=2)

# ════════════════════════════════════════════════════════════
#  GAS ALERT — highest priority interrupt
# ════════════════════════════════════════════════════════════

def on_gas_alert(gas_level: int):
    print(f"\n[!! GAS ALERT !!] Level: {gas_level}")
    speaker.stop()                      # jo bol raha tha roko
    arduino_ctrl.write(b'BUZZER_ON\n')  # buzzer on
    servo_ctrl.alert_pose()

    msg = (
        "KHABARDAR! Gas leak detect hua hai! "
        "Abhi khidki kholo, bijli ke switch mat chhuo, "
        "aur turant bahar jao!"
    )
    speaker.speak(msg, mode="nyro")     # alert hamesha Nyro voice
    arduino_ctrl.write(b'BUZZER_OFF\n')
    servo_ctrl.idle()

# ════════════════════════════════════════════════════════════
#  MODEL SWITCH
# ════════════════════════════════════════════════════════════

def switch_to(new_mode: str):
    global current_mode
    with _mode_lock:
        if current_mode == new_mode: return
        current_mode = new_mode

    # Arduino face change
    if new_mode == "nyro":
        arduino_ctrl.write(b'FACE_NYRO\n')
        servo_ctrl.nod()
        msg = "Theek hai, Nyro wapas aa gaya. Kya poochna hai?"
    else:
        arduino_ctrl.write(b'FACE_BHAI\n')
        servo_ctrl.excited()
        msg = "Abe yaar! Bhai aa gaya! Ab masti shuru hoti hai!"

    print(f"\n{'─'*36}\n  SWITCH → {new_mode.upper()}\n{'─'*36}\n")
    speaker.speak(msg, mode=new_mode)

# ════════════════════════════════════════════════════════════
#  BRAIN WORKER (async Gemini call)
# ════════════════════════════════════════════════════════════

def _brain_worker():
    while True:
        item = _brain_q.get()
        if item is None: break
        heard, mode = item
        try:
            # Sensor data refresh karo brain ko
            t, h = sensor_ctrl.get_temp_humidity()
            g    = sensor_ctrl.get_gas()
            brain.update_sensor_data(t, h, g)

            reply = brain.get_reply(heard, mode=mode)
            if not _reply_q.full():
                _reply_q.put((heard, reply, mode))
        except Exception as e:
            print(f"[Brain Worker] {e}")
        _brain_q.task_done()

# ════════════════════════════════════════════════════════════
#  SPEAKER WORKER (async TTS + Arduino)
# ════════════════════════════════════════════════════════════

def _speaker_worker():
    while True:
        item = _reply_q.get()
        if item is None: break
        heard, reply, mode = item
        print(f"[User]  {heard}")
        print(f"[{mode.upper()}] {reply}\n")
        speaker.speak(reply, mode=mode)
        _reply_q.task_done()

# ════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════

def main():
    global current_mode

    print("\n" + "═"*44)
    print("   NYRO v4 — Dual Model AI Robot")
    print("   Model 1: Nyro | Model 2: Bhai")
    print("   Kshitij ka project — education & fun")
    print("═"*44 + "\n")

    # Hardware init
    arduino_ctrl.connect()
    servo_ctrl.init()
    sensor_ctrl.start()
    sensor_ctrl.set_alert_callback(on_gas_alert)

    # Async worker threads
    threading.Thread(target=_brain_worker,   daemon=True).start()
    threading.Thread(target=_speaker_worker, daemon=True).start()

    # Listener start
    listener.start(stop_callback=speaker.stop)

    # Startup face + greeting
    if current_mode == "nyro":
        arduino_ctrl.write(b'FACE_NYRO\n')
    else:
        arduino_ctrl.write(b'FACE_BHAI\n')

    name    = memory.get("name")
    greet   = (
        f"Wapas aa gaye {name}! Main taiyaar hoon." if name
        else "Namaste! Main Nyro hoon. Kya poochna hai?"
    )
    servo_ctrl.wave()
    speaker.speak(greet, mode=current_mode)

    print(f"[Main] Listening — Mode: {current_mode.upper()}")
    print("  'switch bhai'  → Fun mode | 'switch nyro' → Serious mode\n")

    try:
        while True:
            heard = listener.get(timeout=0.4)
            if not heard: continue

            low = heard.lower()

            # Switch check pehle
            if any(w in low for w in TRIGGER_NYRO):
                threading.Thread(target=switch_to, args=("nyro",), daemon=True).start()
                continue
            if any(w in low for w in TRIGGER_BHAI):
                threading.Thread(target=switch_to, args=("bhai",), daemon=True).start()
                continue

            # Baaki input brain ko bhejo
            with _mode_lock:
                mode_now = current_mode
            if not _brain_q.full():
                _brain_q.put((heard, mode_now))

    except KeyboardInterrupt:
        print("\n[Main] Shutting down...")
    finally:
        _brain_q.put(None)
        _reply_q.put(None)
        listener.stop()
        speaker.stop()
        arduino_ctrl.write(b'BUZZER_OFF\n')
        arduino_ctrl.close()
        servo_ctrl.cleanup()
        print("[Main] Nyro v4 band ho gaya. Bye!")

if __name__ == "__main__":
    main()
