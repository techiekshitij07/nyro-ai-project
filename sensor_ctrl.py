# sensor_ctrl.py — Nyro v4 — DHT11 + Gas Sensor
# DHT11: temperature + humidity (GPIO 4)
# MQ-2 gas: via MCP3008 SPI ADC
# Background thread — never blocks main loop
# -*- coding: utf-8 -*-
import time, threading
from config import DHT_PIN, GAS_ADC_CHANNEL, GAS_THRESHOLD, GAS_COOLDOWN

# ── Shared state ──────────────────────────────────────────────
_state = {
    "temp":      None,
    "humidity":  None,
    "gas":       0,
    "gas_alert": False,
}
_lock        = threading.Lock()
_alert_cb    = None    # main.py sets this
_last_alert  = 0

def set_alert_callback(fn):
    global _alert_cb
    _alert_cb = fn

def get_temp_humidity():
    with _lock:
        return _state["temp"], _state["humidity"]

def get_gas():
    with _lock:
        return _state["gas"]

def is_gas_alert():
    with _lock:
        return _state["gas_alert"]

def get_all():
    with _lock:
        return dict(_state)

# ── DHT11 read ────────────────────────────────────────────────
def _read_dht():
    try:
        import adafruit_dht, board
        sensor = adafruit_dht.DHT11(getattr(board, f"D{DHT_PIN}"))
        t = sensor.temperature
        h = sensor.humidity
        sensor.exit()
        if t is not None and h is not None:
            return round(float(t), 1), round(float(h), 1)
    except ImportError:
        # Simulation for testing without hardware
        import random
        return round(22 + random.uniform(-2, 8), 1), round(50 + random.uniform(-10, 20), 1)
    except Exception:
        pass
    return None, None

# ── MQ-2 via MCP3008 SPI ─────────────────────────────────────
def _read_gas():
    try:
        import spidev
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = 1350000
        r = spi.xfer2([1, (8 + GAS_ADC_CHANNEL) << 4, 0])
        val = ((r[1] & 3) << 8) + r[2]
        spi.close()
        return val
    except ImportError:
        import random
        return random.randint(30, 200)  # simulation
    except Exception:
        return 0

# ── Background loop ───────────────────────────────────────────
def _loop():
    global _last_alert
    dht_timer = 0
    while True:
        now = time.time()

        # DHT11 — read every 3 sec (sensor minimum interval)
        if now - dht_timer >= 3:
            t, h = _read_dht()
            with _lock:
                if t is not None:
                    _state["temp"]     = t
                    _state["humidity"] = h
            dht_timer = now

        # Gas — read every 1 sec
        gas = _read_gas()
        with _lock:
            _state["gas"] = gas
            alert_trigger  = (
                gas > GAS_THRESHOLD and
                (now - _last_alert) > GAS_COOLDOWN
            )
            if alert_trigger:
                _state["gas_alert"] = True
                _last_alert = now
            else:
                _state["gas_alert"] = gas > GAS_THRESHOLD

        if alert_trigger and _alert_cb:
            threading.Thread(target=_alert_cb, args=(gas,), daemon=True).start()

        time.sleep(1)

def start():
    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    print("[Sensor] DHT11 + MQ-2 loop started.")
