#!/bin/bash
# install.sh — Nyro v4 Final — Raspberry Pi 3B+ Installer
# Ek baar chalao, sab ready
# SSH se ya Thonny terminal mein:  bash install.sh

set -e
G='\033[0;32m'; Y='\033[1;33m'; B='\033[1;34m'; R='\033[0;31m'; N='\033[0m'
ok()   { echo -e "${G}[OK]${N} $1"; }
info() { echo -e "${B}[>>]${N} $1"; }
warn() { echo -e "${Y}[!!]${N} $1"; }

NYRO_DIR="$HOME/nyro_v4"
VENV="$NYRO_DIR/venv"
PIPER_DIR="$HOME/piper"
SRC="$(cd "$(dirname "$0")" && pwd)"

echo -e "\n${B}╔═══════════════════════════════╗"
echo -e "║  NYRO v4 — Pi Installer       ║"
echo -e "╚═══════════════════════════════╝${N}\n"

# ── System packages ───────────────────────────────────────────
info "System packages install..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3 python3-pip python3-venv \
    portaudio19-dev mpg123 alsa-utils flac git wget \
    libatlas-base-dev libasound2-dev pigpio python3-pigpio \
    2>/dev/null
ok "System packages done"

# ── Enable SPI (MCP3008 gas sensor ke liye) ──────────────────
info "SPI enable check..."
if ! grep -q "^dtparam=spi=on" /boot/config.txt; then
    echo "dtparam=spi=on" | sudo tee -a /boot/config.txt
    warn "SPI enabled — reboot required after install"
fi
ok "SPI configured"

# ── Files copy ────────────────────────────────────────────────
mkdir -p "$NYRO_DIR"
[ "$SRC" != "$NYRO_DIR" ] && cp "$SRC"/*.py "$NYRO_DIR/" 2>/dev/null || true
ok "Files in $NYRO_DIR"

# ── Python venv ───────────────────────────────────────────────
info "Python venv..."
[ ! -d "$VENV" ] && python3 -m venv "$VENV" --system-site-packages
source "$VENV/bin/activate"
pip install --upgrade pip -q
ok "venv: $VENV"

# ── Python packages ───────────────────────────────────────────
info "Python packages (4-6 min on Pi)..."
pip install -q \
    SpeechRecognition \
    pyaudio \
    gTTS \
    edge-tts \
    google-generativeai \
    pyserial \
    RPi.GPIO \
    adafruit-circuitpython-dht \
    spidev
ok "Python packages done"

# ── Piper TTS (offline Hindi female voice) ────────────────────
info "Piper TTS install..."
PIPER_BIN="$PIPER_DIR/piper"
PIPER_MOD="$PIPER_DIR/hi_IN-female-medium.onnx"

if [ ! -f "$PIPER_BIN" ]; then
    mkdir -p "$PIPER_DIR"
    ARCH=$(uname -m)
    URL="https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_aarch64.tar.gz"
    [ "$ARCH" != "aarch64" ] && URL="${URL/aarch64/armv7l}"
    info "Piper binary download (~15MB)..."
    if wget -q -O /tmp/piper.tar.gz "$URL"; then
        tar -xzf /tmp/piper.tar.gz -C "$PIPER_DIR" --strip-components=1
        rm -f /tmp/piper.tar.gz
        ok "Piper binary: $PIPER_BIN"
    else
        warn "Piper download fail — gTTS fallback chalega"
    fi
fi

if [ ! -f "$PIPER_MOD" ] && [ -f "$PIPER_BIN" ]; then
    info "Hindi voice model download (~65MB)..."
    BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/female/medium"
    wget -q -O "$PIPER_MOD"          "$BASE/hi_IN-female-medium.onnx"
    wget -q -O "${PIPER_MOD}.json"   "$BASE/hi_IN-female-medium.onnx.json"
    ok "Hindi voice model ready"
fi

# Update config.py with actual Piper paths
if [ -f "$PIPER_BIN" ] && [ -f "$PIPER_MOD" ]; then
    sed -i "s|PIPER_BIN.*=.*|PIPER_BIN       = \"$PIPER_BIN\"|" "$NYRO_DIR/config.py"
    sed -i "s|PIPER_MODEL.*=.*|PIPER_MODEL     = \"$PIPER_MOD\"|" "$NYRO_DIR/config.py"
    ok "config.py Piper paths updated"
fi

# ── start_nyro.sh ─────────────────────────────────────────────
cat > "$NYRO_DIR/start_nyro.sh" << 'LAUNCH'
#!/bin/bash
# Nyro v4 Quick Start
cd "$HOME/nyro_v4"
source venv/bin/activate
echo ""
echo "  ╔═════════════════════════╗"
echo "  ║   NYRO v4 Starting...  ║"
echo "  ╚═════════════════════════╝"
echo ""
python3 main.py
LAUNCH
chmod +x "$NYRO_DIR/start_nyro.sh"
ok "start_nyro.sh ready"

# ── Systemd auto-start ────────────────────────────────────────
info "Systemd service (boot par auto-start)..."
sudo tee /etc/systemd/system/nyro.service > /dev/null << SVC
[Unit]
Description=Nyro v4 AI Robot
After=network.target sound.target pigpio.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$NYRO_DIR
ExecStart=$VENV/bin/python3 $NYRO_DIR/main.py
Restart=on-failure
RestartSec=8
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SVC

sudo systemctl daemon-reload
sudo systemctl enable nyro
ok "Systemd service enabled"

# ── Audio test ────────────────────────────────────────────────
if aplay -l 2>/dev/null | grep -q "card"; then
    ok "Audio device detected"
else
    warn "Audio device nahi mila — speaker check karo"
fi

echo ""
echo -e "${G}╔════════════════════════════════════╗"
echo -e "║   NYRO v4 INSTALL COMPLETE!        ║"
echo -e "╚════════════════════════════════════╝${N}"
echo ""
echo -e "  ${Y}bash ~/nyro_v4/start_nyro.sh${N}   ← chalao"
echo -e "  ${Y}sudo systemctl start nyro${N}       ← ya systemd se"
echo -e "  ${Y}journalctl -u nyro -f${N}           ← logs dekhne ke liye"
echo ""
echo -e "  ${B}Arduino mein upload karo:${N}  arduino/nyro_face/nyro_face.ino"
echo ""
echo -e "  ${B}GPIO wiring:${N}"
echo -e "    DHT11 Data  → GPIO 4  (Pin 7)"
echo -e "    Servo Left  → GPIO 17 (Pin 11)"
echo -e "    Servo Right → GPIO 27 (Pin 13)"
echo -e "    MCP3008 SPI → GPIO 8,9,10,11"
echo -e "    Arduino Mega→ USB /dev/ttyACM0"
echo ""
