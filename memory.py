# memory.py — Nyro v3 Persistent Memory
# -*- coding: utf-8 -*-
import os, json
from config import MEM_FILE

_mem = {}

def load():
    global _mem
    if os.path.exists(MEM_FILE):
        try:
            with open(MEM_FILE, "r", encoding="utf-8") as f:
                _mem = json.load(f)
        except:
            _mem = {}
    return _mem

def save():
    with open(MEM_FILE, "w", encoding="utf-8") as f:
        json.dump(_mem, f, ensure_ascii=False, indent=2)

def get(key, default=""):
    return _mem.get(key, default)

def set(key, value):
    _mem[key] = value
    save()

def get_context_string():
    """Brain.py ko context deta hai — user ka naam, mood, last topic."""
    parts = []
    if _mem.get("name"):
        parts.append(f"User ka naam: {_mem['name']}")
    if _mem.get("mood"):
        parts.append(f"User ka mood: {_mem['mood']}")
    if _mem.get("last_topic"):
        parts.append(f"Pichla topic: {_mem['last_topic']}")
    return " | ".join(parts) if parts else ""

# Auto-load on import
load()
