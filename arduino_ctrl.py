# arduino_ctrl.py — Nyro v3 Arduino Serial Controller
# -*- coding: utf-8 -*-
import serial, time
from config import SERIAL_PORT, SERIAL_BAUD

_ser = None

def connect():
    global _ser
    try:
        _ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
        time.sleep(1.5)   # Arduino reset ka wait
        print(f"[Arduino] Connected on {SERIAL_PORT}")
    except Exception as e:
        print(f"[Arduino] Not connected ({e}) — animation disabled")
        _ser = None

def write(cmd: bytes):
    try:
        if _ser and _ser.is_open:
            _ser.write(cmd)
            _ser.flush()
    except:
        pass

def close():
    try:
        if _ser:
            _ser.close()
    except:
        pass

connect()   # Import hote hi auto-connect
