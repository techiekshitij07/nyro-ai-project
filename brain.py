# brain.py — Nyro v4 — Two AI Models
# Model 1: Nyro  — serious, health, sensors, problem solver
# Model 2: Bhai  — fun, masti, games, bakchodi
# -*- coding: utf-8 -*-
import re, random
import google.generativeai as genai
import memory
from config import (
    GEMINI_API_KEY, GEMINI_MODEL,
    MAX_WORDS_NYRO, MAX_WORDS_BHAI, MAX_TOKENS
)

genai.configure(api_key=GEMINI_API_KEY)
_model = genai.GenerativeModel(GEMINI_MODEL)

# ════════════════════════════════════════════════════════════
#  PERSONALITY PROMPTS
# ════════════════════════════════════════════════════════════

_PROMPT_NYRO = (
    "Tu Nyro AI hai — ek real, warm aur intelligent assistant. "
    "Kshitij ne banaya hai tujhe. Hindi ya Hinglish mein bol. "
    "'Hmm', 'acha dekho', 'sunno' jaisi expressions use kar — insaan jaisa. "
    "Comma aur full stop se natural pause aane chahiye speech mein. "
    "Health topics, science, general knowledge, life advice — sab samjha sakta hai. "
    "Agar sensor data context mein diya ho toh naturally use kar. "
    "Medical advice ke liye doctor refer karna mat bhoolna — pyaar se. "
    "50 words mein clear jawab de. Abruptly mat khatam kar."
)

_PROMPT_BHAI = (
    "Tu 'Bhai' hai — Kshitij ka sabse mast, funny dost. "
    "College wali yaari — full bakchodi, lekin dil ka seedha. "
    "'Abe yaar', 'chal na bhai', 'kya bol raha hai' bolna teri aadat hai. "
    "Jokes maar, thoda roast kar, sab kuch funny bana — lekin loving. "
    "Game chal raha ho toh game pe focus kar. "
    "45 words, punchy aur natural. Robotic mat ban."
)

# ════════════════════════════════════════════════════════════
#  NUMBER GAME STATE
# ════════════════════════════════════════════════════════════
_game = {"active": False, "secret": 0, "tries": 0, "result": ""}

def game_start():
    _game.update({"active": True, "secret": random.randint(1, 20),
                  "tries": 0, "result": ""})
    return True

def game_guess(n: int) -> str:
    _game["tries"] += 1
    s = _game["secret"]
    if n == s:
        _game["result"] = f"Sahi! {_game['tries']} mein"
        _game["active"] = False
        return "correct"
    return "high" if n > s else "low"

def game_active() -> bool:
    return _game["active"]

def game_state() -> dict:
    return dict(_game)

# ════════════════════════════════════════════════════════════
#  SENSOR DATA INJECTOR
# ════════════════════════════════════════════════════════════
_sensor_data = {"temp": None, "humidity": None, "gas": 0}

def update_sensor_data(temp, humidity, gas):
    _sensor_data.update({"temp": temp, "humidity": humidity, "gas": gas})

# ════════════════════════════════════════════════════════════
#  FAST HARDCODED REPLIES (saves API call)
# ════════════════════════════════════════════════════════════

def _quick(text: str, mode: str):
    low = text.lower()

    # Identity
    if any(w in low for w in ["tum kaun ho","kon ho","who are you","tumhara naam","creator","made you"]):
        if mode == "bhai":
            return "Abe yaar main Bhai hoon! Kshitij boss ne banaya — kya insaan hai!"
        return "Main Nyro hoon, Kshitij ne banaya. Kya kaam hai?"

    # Name
    if "mera naam" in low:
        words = text.split()
        name = words[-1] if len(words) > 2 else "dost"
        memory.set("name", name)
        return f"Arre {name} bhai, yaad kar liya!" if mode == "bhai" else f"Theek hai {name}, maine note kar liya."

    # Recall name
    if "yaad hai" in low or "remember me" in low:
        n = memory.get("name")
        return (f"Abe {n} ka naam bhooloon?!" if mode == "bhai" else f"Haan, tum {n} ho!") if n else "Naam batao pehle!"

    # Temperature / humidity — DHT11 live data
    if any(w in low for w in ["temperature","temp","tapman","garmi","thand","aaj ka mausam","kitni garmi","humidity","aardrata"]):
        t  = _sensor_data["temp"]
        h  = _sensor_data["humidity"]
        if t is not None:
            if mode == "bhai":
                feel = "mast" if 20 <= t <= 28 else ("bahut garmi" if t > 28 else "thand")
                return f"Abe yaar abhi {t}°C hai aur humidity {h}% — {feel} hai bahar!"
            return f"Abhi temperature {t}°C aur humidity {h}% hai."
        return "Sensor data abhi nahi mila, thoda ruko." if mode == "nyro" else "Abe sensor thoda so raha hai yaar, wait karo!"

    # Gas safety check
    if any(w in low for w in ["gas","suraksha","safe hai"]):
        from config import GAS_THRESHOLD
        g = _sensor_data["gas"]
        if g > GAS_THRESHOLD:
            return "KHABARDAR! Gas detect hua! Khidki kholo, bahar jao!"
        return "Gas level bilkul normal hai." if mode == "nyro" else "Chill bhai, sab safe hai!"

    # Mood
    if any(w in low for w in ["udaas","sad hoon","dukhi","bura lag"]):
        memory.set("mood", "sad")
        return "Abe kya hua yaar? Bata, main hoon na!" if mode == "bhai" else "Kya hua? Baat karo, main hoon."

    if any(w in low for w in ["khush hoon","mast hoon","badhiya"]):
        memory.set("mood", "happy")
        return "Waah yaar, mast raho!" if mode == "bhai" else "Bahut achha! Khush raho hamesha."

    # Game commands (Bhai mode)
    if mode == "bhai":
        if any(w in low for w in ["game khelo","game chalao","number game","khelten hain"]):
            game_start()
            return "Chalo yaar game shuru! 1 se 20 ke beech ek number socho aur bolo!"

        if any(w in low for w in ["game band","game off","game khatam","game chodo"]):
            _game["active"] = False
            return "Game band! Wapas masti mein? Bolo bhai!"

        if _game["active"]:
            nums = re.findall(r'\d+', text)
            if nums:
                n = int(nums[0])
                if not (1 <= n <= 20):
                    return "Abe 1 se 20 ke beech bolo yaar!"
                res = game_guess(n)
                if res == "correct":
                    return f"WAAH! Sahi! {_game['result']} tries mein pakad liya — tu toh genius hai yaar!"
                return f"Naah yaar, aur {'kam' if res == 'high' else 'zyada'} bolo! Try {_game['tries']} hua."

    return None  # AI call karo

# ════════════════════════════════════════════════════════════
#  TEXT CLEANER
# ════════════════════════════════════════════════════════════

def _clean(t: str, limit: int) -> str:
    t = re.sub(r"[^a-zA-Z0-9\u0900-\u097F\s\.,!?]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return " ".join(t.split()[:limit]).strip()

# ════════════════════════════════════════════════════════════
#  MAIN REPLY
# ════════════════════════════════════════════════════════════

def get_reply(user_text: str, mode: str = "nyro") -> str:
    quick = _quick(user_text, mode)
    if quick:
        return quick

    ctx = ""
    n = memory.get("name")
    if n: ctx += f"User ka naam: {n}. "
    mood = memory.get("mood")
    if mood: ctx += f"User ka mood: {mood}. "
    t = _sensor_data["temp"]
    if t: ctx += f"Room temp: {t}°C. "

    sys_prompt = _PROMPT_NYRO if mode == "nyro" else _PROMPT_BHAI
    if ctx:
        sys_prompt += f"\n[Context: {ctx}]"

    full = f"{sys_prompt}\nUser: {user_text}\nReply:"
    lim  = MAX_WORDS_NYRO if mode == "nyro" else MAX_WORDS_BHAI

    try:
        resp = _model.generate_content(
            full,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=MAX_TOKENS,
                temperature=0.88 if mode == "bhai" else 0.70,
            )
        )
        ans = getattr(resp, "text", "") or ""
    except Exception as e:
        print(f"[Brain] API error: {e}")
        ans = "Yaar abhi dimag thoda atak gaya, dobara bolo." if mode == "bhai" \
              else "Abhi jawab nahi aa raha, thodi der mein try karo."

    memory.set("last_topic", user_text[:40])
    return _clean(ans, lim)
