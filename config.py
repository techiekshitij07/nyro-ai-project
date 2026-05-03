# config.py — Nyro v4 Final — All Settings
# -*- coding: utf-8 -*-

# ── Gemini AI ─────────────────────────────────────────────────
GEMINI_API_KEY = "AIzaSyAc8MyXwoQPlK39LUqC5xHsLjeWaii25uc"
GEMINI_MODEL   = "models/gemini-2.5-flash"

# ── Serial (Arduino Mega) ──────────────────────────────────────
ARDUINO_PORT = "/dev/ttyACM0"
ARDUINO_BAUD = 9600

# ── GPIO ──────────────────────────────────────────────────────
DHT_PIN         = 4    # DHT11 data → GPIO4
SERVO_LEFT_PIN  = 17   # Left arm servo → GPIO17
SERVO_RIGHT_PIN = 27   # Right arm servo → GPIO27
SERVO_FREQ      = 50   # Hz

# ── Gas sensor (MQ-2 → MCP3008 SPI ADC) ──────────────────────
GAS_ADC_CHANNEL = 0
GAS_THRESHOLD   = 450   # 0-1023, ADC raw value
GAS_COOLDOWN    = 30    # seconds between alerts

# ── TTS (100% OFFLINE PIPER) ──────────────────────────────────
TTS_ENGINE       = "piper"
PIPER_BIN        = "/home/pi/piper/piper"

# Nyro ke liye: Priyamvada (Natural Female Voice)
PIPER_MODEL_NYRO = "/home/pi/piper/hi_IN-priyamvada-medium.onnx"

# Bhai ke liye: Rohan (Real Human Male Voice)
PIPER_MODEL_BHAI = "/home/pi/piper/hi_IN-rohan-medium.onnx"

# Shared audio output
AUDIO_WAV  = "/tmp/nyro.wav"
AUDIO_MP3  = "/tmp/nyro.mp3"

# ── Speech recognition ────────────────────────────────────────
LANG_RECOG   = "hi-IN"
PHRASE_LIMIT = 5    # seconds
STOP_WORDS   = ["chup", "shant", "band karo", "stop"]
MODE_TRIGGERS = {
    "switch nyro": "nyro", "hello nyro": "nyro", "nyro aa jao": "nyro", "serious mode": "nyro",
    "switch bhai": "bhai", "bhai aa jao": "bhai", "masti mode": "bhai", "fun mode": "bhai"
}

# ── Response limits ───────────────────────────────────────────
MAX_WORDS_NYRO = 50
MAX_WORDS_BHAI = 45
MAX_TOKENS     = 130

# ── Memory ────────────────────────────────────────────────────
MEM_FILE = "/home/pi/nyro_v4/memory.json"

# ── Default start mode ────────────────────────────────────────
DEFAULT_MODE = "nyro"    # "nyro" | "bhai"
