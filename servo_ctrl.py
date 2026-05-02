# servo_ctrl.py — Nyro v4 Servo Motor Controller
# 2 servo motors — left + right hand/arm
# Body language: wave, nod, point, excited, idle
# -*- coding: utf-8 -*-
import time, threading
from config import SERVO_LEFT_PIN, SERVO_RIGHT_PIN, SERVO_FREQ

# ── GPIO PWM ─────────────────────────────────────────────────
_left  = None
_right = None
_lock  = threading.Lock()

def _duty(angle):
    """Angle (0-180) → PWM duty cycle for standard servo."""
    return 2.5 + (angle / 180.0) * 10.0

def init():
    global _left, _right
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SERVO_LEFT_PIN,  GPIO.OUT)
        GPIO.setup(SERVO_RIGHT_PIN, GPIO.OUT)
        _left  = GPIO.PWM(SERVO_LEFT_PIN,  SERVO_FREQ)
        _right = GPIO.PWM(SERVO_RIGHT_PIN, SERVO_FREQ)
        _left.start(0)
        _right.start(0)
        print("[Servo] GPIO initialized.")
    except ImportError:
        print("[Servo] RPi.GPIO nahi hai — simulation mode.")
    except Exception as e:
        print(f"[Servo] Init error: {e}")

def _move(servo, angle, hold=0.3):
    if servo is None: return
    servo.ChangeDutyCycle(_duty(angle))
    time.sleep(hold)
    servo.ChangeDutyCycle(0)   # jitter band karo

def _run(fn):
    threading.Thread(target=fn, daemon=True).start()

# ════════════════════════════════════════════════════════════
#  GESTURE LIBRARY
#  Har gesture ek function hai — background thread mein chalta hai
# ════════════════════════════════════════════════════════════

def idle():
    """Rest position — dono haath neeche."""
    def _go():
        with _lock:
            _move(_left,  90, 0.3)
            _move(_right, 90, 0.3)
    _run(_go)

def wave():
    """Haath hilana — greet / excited / hello."""
    def _go():
        with _lock:
            for _ in range(3):
                _move(_right, 150, 0.15)
                _move(_right, 60,  0.15)
            _move(_right, 90, 0.2)
    _run(_go)

def nod():
    """Dono haath thoda upar-neeche — agree / suno."""
    def _go():
        with _lock:
            for _ in range(2):
                _move(_left,  110, 0.15); _move(_right, 110, 0.15)
                _move(_left,  70,  0.15); _move(_right, 70,  0.15)
            idle()
    _run(_go)

def point_forward():
    """Aage point karna — 'dekho yeh!'"""
    def _go():
        with _lock:
            _move(_right, 30, 0.6)
            time.sleep(0.4)
            idle()
    _run(_go)

def thinking():
    """Ek haath upar — soch raha hoon."""
    def _go():
        with _lock:
            _move(_left, 140, 0.5)
            time.sleep(0.8)
            idle()
    _run(_go)

def excited():
    """Dono haath hilana — masti/khushi."""
    def _go():
        with _lock:
            for _ in range(4):
                _move(_left,  150, 0.1); _move(_right, 30,  0.1)
                _move(_left,  30,  0.1); _move(_right, 150, 0.1)
            idle()
    _run(_go)

def shrug():
    """Dono kaandhon ko utha ke — 'pata nahi'."""
    def _go():
        with _lock:
            _move(_left,  120, 0.4); _move(_right, 120, 0.4)
            time.sleep(0.5)
            idle()
    _run(_go)

def alert_pose():
    """Gas alert — dono haath upar attention pose."""
    def _go():
        with _lock:
            for _ in range(2):
                _move(_left,  160, 0.2); _move(_right, 160, 0.2)
                _move(_left,  90,  0.2); _move(_right, 90,  0.2)
    _run(_go)

# ════════════════════════════════════════════════════════════
#  CONTEXT-BASED GESTURE PICKER
# ════════════════════════════════════════════════════════════
def gesture_for(text: str, mode: str):
    """
    Text aur mode ke hisaab se sahi gesture choose karo.
    speaker.py ise call karega bolne se pehle.
    """
    low = text.lower()
    if mode == "bhai":
        if any(w in low for w in ["waah", "mast", "badhiya", "yaar", "bhai"]):
            return excited
        if any(w in low for w in ["pata nahi", "hmm", "soch"]):
            return thinking
        return wave   # bhai mode mein default wave
    else:
        # nyro (serious) mode
        if any(w in low for w in ["namaste", "hello", "wapas", "aa gaya"]):
            return wave
        if any(w in low for w in ["dekho", "yeh hai", "suno"]):
            return point_forward
        if any(w in low for w in ["haan", "bilkul", "sahi"]):
            return nod
        if any(w in low for w in ["pata nahi", "sorry", "nahi samjha"]):
            return shrug
    return None   # gesture nahi — idle rahega

def cleanup():
    try:
        import RPi.GPIO as GPIO
        if _left:  _left.stop()
        if _right: _right.stop()
        GPIO.cleanup()
    except: pass
