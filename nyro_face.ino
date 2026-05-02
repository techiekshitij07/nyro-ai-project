// nyro_face_v4.ino — Arduino Mega + TFT
// Adafruit_GFX + MCUFRIEND_kbv + math.h
//
// MODEL 1 — NYRO: 100% original face (exact tumhara code)
// MODEL 2 — BHAI: organic round expressive cartoon face
//
// Serial from Raspberry Pi:
//   START_SPEECH / END_SPEECH / FACE_NYRO / FACE_BHAI
//   BUZZER_ON / BUZZER_OFF

#include <Adafruit_GFX.h>
#include <MCUFRIEND_kbv.h>
#include <math.h>

MCUFRIEND_kbv tft;

// ── Colors (original set kept) ───────────────────────────────
#define BLACK     0x0000
#define WHITE     0xFFFF
#define SKYBLUE   0x07FF
#define BLUE      0x001F
#define DEEPBLUE  0x0010
#define CYAN      0x07FE
#define PINK      0xF81F
// Bhai extras
#define YELLOW    0xFFE0
#define PURPLE    0x780F
#define DPURPLE   0x400F
#define MPURPLE   0x600F
#define LPINK     0xFDB8
#define CREAM     0xFFF6
#define GOLD      0xFEA0
#define ORANGE    0xFD20

// ── Mode ─────────────────────────────────────────────────────
#define MODE_NYRO 0
#define MODE_BHAI 1
int faceMode = MODE_NYRO;

// ── Face center ───────────────────────────────────────────────
int cx = 160, cy = 120;

// ── Eye state ────────────────────────────────────────────────
int  eyeOffset = 0;
bool eyesClosed = false;
unsigned long lastBlink = 0, lastEyeMove = 0;

// ── Mouth (smooth easing — EXACT original variables) ─────────
bool  mouthTalking = false;
float mouthOpen    = 0.0f;
float mouthTarget  = 0.0f;
float mouthEase    = 0.35f;

const int SYLLABLE_COUNT = 8;
int syllableOpen[SYLLABLE_COUNT] = { 4, 8, 12, 9, 5, 0, 7, 11 };
int syllableDur[SYLLABLE_COUNT]  = { 90, 110, 140, 120, 100, 80, 110, 140 };
int syllableIndex  = 0;
unsigned long syllableStart = 0;

int mouthAreaX = 160 - 80;
int mouthAreaY = 120 + 55 - 50;
int mouthAreaW = 160;
int mouthAreaH = 100;

// ── Bhai extras ───────────────────────────────────────────────
unsigned long lastWink    = 0;
unsigned long lastSparkle = 0;
int sparklePhase          = 0;

// ── Buzzer ───────────────────────────────────────────────────
#define BUZZER_PIN 8
bool buzzerOn = false;
unsigned long lastBeep = 0;

// ════════════════════════════════════════════════════════════
void setup() {
  Serial.begin(9600);
  pinMode(BUZZER_PIN, OUTPUT);
  noTone(BUZZER_PIN);
  uint16_t ID = tft.readID();
  if (ID == 0x0 || ID == 0xFFFF) ID = 0x9486;
  tft.begin(ID);
  tft.setRotation(1);
  drawFaceBase();
}

// ════════════════════════════════════════════════════════════
void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if      (cmd == "START_SPEECH") startSpeech();
    else if (cmd == "END_SPEECH")   endSpeech();
    else if (cmd == "FACE_NYRO")    switchFace(MODE_NYRO);
    else if (cmd == "FACE_BHAI")    switchFace(MODE_BHAI);
    else if (cmd == "BUZZER_ON")  { buzzerOn = true;  tone(BUZZER_PIN, 880); }
    else if (cmd == "BUZZER_OFF") { buzzerOn = false; noTone(BUZZER_PIN); }
  }

  unsigned long now = millis();

  if (now - lastEyeMove > 1200) {
    eyeOffset = random(-4, 5);
    if (faceMode == MODE_NYRO) drawEyes(eyeOffset);
    else                       drawBhaiEyes(eyeOffset);
    lastEyeMove = now;
  }

  if (now - lastBlink > (unsigned long)random(2000, 5000)) {
    blinkEyes();
    lastBlink = now;
  }

  if (faceMode == MODE_BHAI) {
    if (now - lastWink > (unsigned long)random(7000, 15000)) {
      doBhaiWink();
      lastWink = now;
    }
    if (now - lastSparkle > 450) {
      tickSparkles();
      lastSparkle = now;
    }
  }

  if (mouthTalking) {
    if (now - syllableStart >= (unsigned long)syllableDur[syllableIndex]) {
      syllableIndex = (syllableIndex + 1) % SYLLABLE_COUNT;
      syllableStart = now;
      mouthTarget   = syllableOpen[syllableIndex];
    }
  }

  float delta = mouthTarget - mouthOpen;
  mouthOpen  += delta * mouthEase;

  static int lastDrawnOpen = -999;
  int openInt = (int)round(mouthOpen);
  if (openInt != lastDrawnOpen) {
    if (faceMode == MODE_NYRO) drawSmile(openInt);
    else                       drawBhaiMouth(openInt);
    lastDrawnOpen = openInt;
  }

  if (buzzerOn && (now - lastBeep > 600)) {
    tone(BUZZER_PIN, 880, 180);
    lastBeep = now;
  }
}

// ── Speech ───────────────────────────────────────────────────
void startSpeech() {
  mouthTalking  = true;
  syllableIndex = 0;
  syllableStart = millis();
  mouthTarget   = syllableOpen[0];
}

void endSpeech() {
  mouthTalking = false;
  syllableIndex = 0;
  mouthTarget   = 0;
  mouthOpen     = 0;
  if (faceMode == MODE_NYRO) drawSmile(0);
  else                       drawBhaiMouth(0);
}

// ── Switch ────────────────────────────────────────────────────
void switchFace(int m) {
  if (faceMode == m) return;
  faceMode = m;
  endSpeech();
  drawFaceBase();
}

void drawFaceBase() {
  if (faceMode == MODE_NYRO) drawNyroBase();
  else                       drawBhaiBase();
}

// ════════════════════════════════════════════════════════════
//  NYRO FACE — 100% original code, zero changes
// ════════════════════════════════════════════════════════════

void drawNyroBase() {
  for (int y = 0; y < 240; y++) {
    uint16_t shade = (y < 100) ? CYAN : SKYBLUE;
    tft.drawFastHLine(0, y, 320, shade);
  }
  drawEyes(0);
  drawSmile(0);
  tft.fillCircle(cx - 90, cy + 40, 12, PINK);
  tft.fillCircle(cx + 90, cy + 40, 12, PINK);
}

void drawEyes(int offset) {
  int eyeY = cy - 30;
  int lx = cx - 60, rx = cx + 60;
  drawEye(lx, eyeY, offset);
  drawEye(rx, eyeY, offset);
}

void drawEye(int x, int y, int offset) {
  if (eyesClosed) {
    tft.fillRect(x - 32, y - 32, 64, 64, SKYBLUE);
    tft.drawFastHLine(x - 25, y, 50, DEEPBLUE);
    return;
  }
  tft.fillCircle(x, y, 32, WHITE);
  tft.fillCircle(x + offset, y, 26, SKYBLUE);
  tft.fillCircle(x + offset, y, 14, DEEPBLUE);
  tft.fillCircle(x + offset - 6, y - 6, 4, WHITE);
  tft.fillCircle(x + offset - 4, y - 4, 2, WHITE);
}

void drawSmile(int open) {
  int mx = cx, my = cy + 55;
  int r = 40;
  int thickness = 3;
  tft.fillRect(mouthAreaX, mouthAreaY, mouthAreaW, mouthAreaH, SKYBLUE);
  for (int i = 0; i < thickness; i++) {
    for (int angle = 20; angle <= 160; angle += 2) {
      int x1 = mx + (r+i) * cos(radians(angle));
      int y1 = my + (r+i) * sin(radians(angle)) - open;
      int x2 = mx + (r+i) * cos(radians(angle+2));
      int y2 = my + (r+i) * sin(radians(angle+2)) - open;
      tft.drawLine(x1, y1, x2, y2, DEEPBLUE);
    }
  }
  for (int angle = 30; angle <= 150; angle += 3) {
    int x1 = mx + (r - 4) * cos(radians(angle));
    int y1 = my + (r - 4) * sin(radians(angle)) - open;
    int x2 = mx + (r - 4) * cos(radians(angle + 3));
    int y2 = my + (r - 4) * sin(radians(angle + 3)) - open;
    tft.drawLine(x1, y1, x2, y2, BLUE);
  }
}

// ════════════════════════════════════════════════════════════
//  BHAI FACE — organic, round, expressive cartoon
//  All circles + arcs. Zero boxes/rects for features.
// ════════════════════════════════════════════════════════════

void drawBhaiBase() {
  // Deep purple gradient background
  for (int y = 0; y < 240; y++) {
    uint16_t c;
    if      (y < 45)  c = DPURPLE;
    else if (y < 140) c = MPURPLE;
    else if (y < 200) c = PURPLE;
    else              c = DPURPLE;
    tft.drawFastHLine(0, y, 320, c);
  }

  // Gold glow ring behind face
  tft.fillCircle(cx, cy + 4, 106, GOLD);
  // Main face — big warm cream circle
  tft.fillCircle(cx, cy + 4, 100, CREAM);
  // Slight blush overlay on lower face
  for (int r = 98; r > 88; r--) {
    tft.drawCircle(cx, cy + 4, r, LPINK);
  }
  // Ears (round, organic)
  tft.fillCircle(cx - 100, cy + 4, 22, CREAM);
  tft.fillCircle(cx + 100, cy + 4, 22, CREAM);
  tft.fillCircle(cx - 100, cy + 4, 14, LPINK);
  tft.fillCircle(cx + 100, cy + 4, 14, LPINK);

  // Large soft cheek blushes
  tft.fillCircle(cx - 66, cy + 44, 22, LPINK);
  tft.fillCircle(cx + 66, cy + 44, 22, LPINK);

  // Cute small nose — two dots
  tft.fillCircle(cx - 7,  cy + 12, 5, LPINK);
  tft.fillCircle(cx + 7,  cy + 12, 5, LPINK);
  tft.fillCircle(cx,      cy + 16, 4, LPINK);  // bridge

  // Eyes and brows
  drawBhaiEyes(0);
  drawBhaiEyebrows(false);

  // Mouth
  drawBhaiMouth(0);

  // Corner sparkles
  tickSparkles();

  // Name
  tft.setTextColor(YELLOW);
  tft.setTextSize(2);
  tft.setCursor(108, 215);
  tft.print("BHAI");
}

// ── Bhai eyes: big organic circles, huge shine spots ──────────
void drawBhaiEyes(int offset) {
  int ey = cy - 20;
  int lx = cx - 50, rx = cx + 50;

  if (eyesClosed) {
    // Happy closed arc (curved UP = smile eyes)
    tft.fillCircle(lx, ey, 27, CREAM);
    tft.fillCircle(rx, ey, 27, CREAM);
    for (int t = 0; t < 3; t++) {
      for (int a = 195; a <= 345; a += 3) {
        int x1 = lx + (21+t)*cos(radians(a));
        int y1 = ey  + (21+t)*sin(radians(a));
        int x2 = lx + (21+t)*cos(radians(a+3));
        int y2 = ey  + (21+t)*sin(radians(a+3));
        tft.drawLine(x1,y1,x2,y2,DPURPLE);
        tft.drawLine(rx+(x1-lx),y1,rx+(x2-lx),y2,DPURPLE);
      }
    }
    return;
  }

  // White sclera
  tft.fillCircle(lx, ey, 27, WHITE);
  tft.fillCircle(rx, ey, 27, WHITE);
  // Iris — rich purple
  tft.fillCircle(lx + offset, ey, 19, MPURPLE);
  tft.fillCircle(rx + offset, ey, 19, MPURPLE);
  // Inner iris ring
  tft.fillCircle(lx + offset, ey, 14, DPURPLE);
  tft.fillCircle(rx + offset, ey, 14, DPURPLE);
  // Pupil
  tft.fillCircle(lx + offset, ey, 8, BLACK);
  tft.fillCircle(rx + offset, ey, 8, BLACK);
  // Big main shine
  tft.fillCircle(lx + offset - 8, ey - 8, 6, WHITE);
  tft.fillCircle(rx + offset - 8, ey - 8, 6, WHITE);
  // Small secondary shine
  tft.fillCircle(lx + offset + 6, ey - 5, 3, WHITE);
  tft.fillCircle(rx + offset + 6, ey - 5, 3, WHITE);
  // Soft lower lash dots
  for (int a = 20; a <= 160; a += 12) {
    int px = lx + 25*cos(radians(a));
    int py = ey + 25*sin(radians(a));
    tft.fillCircle(px, py, 2, DPURPLE);
    tft.fillCircle(rx + (px - lx), py, 2, DPURPLE);
  }
}

// ── Bhai eyebrows: thick organic arcs above eyes ──────────────
void drawBhaiEyebrows(bool raised) {
  int ey = cy - 20;
  int lx = cx - 50, rx = cx + 50;
  int lift = raised ? -7 : 0;

  // Each brow: thick arc, 5px wide, curved up
  for (int t = 0; t < 5; t++) {
    for (int a = 215; a <= 325; a += 2) {
      float ra1 = radians(a), ra2 = radians(a+2);
      int r2 = 26 + t;
      // Left brow
      int x1 = lx + r2*cos(ra1), y1 = ey - 30 + lift + r2*sin(ra1);
      int x2 = lx + r2*cos(ra2), y2 = ey - 30 + lift + r2*sin(ra2);
      tft.drawLine(x1, y1, x2, y2, DPURPLE);
      // Right brow (mirror)
      tft.drawLine(2*cx - x1, y1, 2*cx - x2, y2, DPURPLE);
    }
  }
}

// ── Bhai mouth: big organic grin + inner arc + teeth + dimples ─
void drawBhaiMouth(int open) {
  // Clear area — face color
  tft.fillRect(mouthAreaX - 10, mouthAreaY, mouthAreaW + 20, mouthAreaH, CREAM);
  // Restore cheeks + nose over cleared area
  tft.fillCircle(cx - 66, cy + 44, 22, LPINK);
  tft.fillCircle(cx + 66, cy + 44, 22, LPINK);
  tft.fillCircle(cx - 7, cy + 12, 5, LPINK);
  tft.fillCircle(cx + 7, cy + 12, 5, LPINK);
  tft.fillCircle(cx,     cy + 16, 4, LPINK);

  int mx = cx, my = cy + 52;
  int r  = 44;

  // Outer grin arc — 5px thick, dark purple
  for (int t = 0; t < 5; t++) {
    for (int a = 12; a <= 168; a += 2) {
      float ra1 = radians(a), ra2 = radians(a+2);
      int x1 = mx + (r+t)*cos(ra1),  y1 = my + (r+t)*sin(ra1) - open;
      int x2 = mx + (r+t)*cos(ra2),  y2 = my + (r+t)*sin(ra2) - open;
      tft.drawLine(x1, y1, x2, y2, DPURPLE);
    }
  }

  // Teeth when open > 4
  if (open > 4) {
    int th = constrain(open - 2, 0, 16);
    int ty = my - open + 8;
    // White fill
    tft.fillRect(mx - 34, ty, 68, th, WHITE);
    // Tooth gap lines — soft gray
    for (int i = -22; i <= 22; i += 11) {
      tft.drawFastVLine(mx + i, ty + 1, th - 2, 0xC618);
    }
  }

  // Inner arc — softer lip feel
  for (int t = 0; t < 3; t++) {
    for (int a = 20; a <= 160; a += 3) {
      float ra1 = radians(a), ra2 = radians(a+3);
      int x1 = mx + (r-10+t)*cos(ra1), y1 = my + (r-10+t)*sin(ra1) - open;
      int x2 = mx + (r-10+t)*cos(ra2), y2 = my + (r-10+t)*sin(ra2) - open;
      tft.drawLine(x1, y1, x2, y2, MPURPLE);
    }
  }

  // Dimple circles at grin corners
  tft.fillCircle(mx + r*cos(radians(12)),  my + r*sin(radians(12))  - open, 6, LPINK);
  tft.fillCircle(mx + r*cos(radians(168)), my + r*sin(radians(168)) - open, 6, LPINK);
}

// ── Wink: right eye only winks, brow raises ───────────────────
void doBhaiWink() {
  int ey = cy - 20;
  int rx = cx + 50;
  // Erase right eye area
  tft.fillCircle(rx, ey, 29, CREAM);
  // Happy curved closed eye
  for (int t = 0; t < 3; t++) {
    for (int a = 195; a <= 345; a += 3) {
      int x1 = rx + (21+t)*cos(radians(a));
      int y1 = ey + (21+t)*sin(radians(a));
      int x2 = rx + (21+t)*cos(radians(a+3));
      int y2 = ey + (21+t)*sin(radians(a+3));
      tft.drawLine(x1, y1, x2, y2, DPURPLE);
    }
  }
  // Mini star near wink
  miniStar(rx + 34, ey - 20, YELLOW);
  delay(400);
  // Restore
  drawBhaiEyes(eyeOffset);
  drawBhaiEyebrows(false);
}

// ── Sparkle tick: 4-point stars twinkling in bg corners ───────
void tickSparkles() {
  int sx[] = {16, 298, 22, 292, 160};
  int sy[] = {16,  16, 205, 205,  8};
  uint16_t sc[] = {YELLOW, GOLD, WHITE, YELLOW, GOLD};
  for (int i = 0; i < 5; i++) {
    uint16_t bg = (sy[i] < 45) ? DPURPLE : (sy[i] < 140 ? MPURPLE : PURPLE);
    tft.fillRect(sx[i]-10, sy[i]-10, 20, 20, bg);
    if ((sparklePhase + i) % 3 != 0)
      miniStar(sx[i], sy[i], sc[i]);
  }
  sparklePhase = (sparklePhase + 1) % 6;
}

void miniStar(int x, int y, uint16_t col) {
  int r1 = 8, r2 = 3;
  for (int i = 0; i < 8; i++) {
    float a1 = radians(i * 45);
    float a2 = radians((i+1) * 45);
    int ri  = (i%2==0)? r1 : r2;
    int ri2 = (i%2==0)? r2 : r1;
    tft.drawLine(x+ri*cos(a1), y+ri*sin(a1), x+ri2*cos(a2), y+ri2*sin(a2), col);
  }
  tft.fillCircle(x, y, 2, col);
}

void blinkEyes() {
  eyesClosed = true;
  if (faceMode == MODE_NYRO) drawEyes(eyeOffset);
  else                       drawBhaiEyes(eyeOffset);
  delay(115);
  eyesClosed = false;
  if (faceMode == MODE_NYRO) drawEyes(eyeOffset);
  else                       drawBhaiEyes(eyeOffset);
}
