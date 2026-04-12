// ════════════════════════════════════════════════════════════════
//  LINE FOLLOW TEST — ESP32 #2
//  Receives IR data from ESP32 #1 via ESP-NOW
//  Controls TB6612FNG motor driver
//
//  WIRING:
//  D25 → PWMA   D26 → AIN1   D27 → AIN2
//  D32 → PWMB   D33 → BIN1   D13 → BIN2
//  D15 → STBY   3V3 → VCC    12V → VM
//
//  LOGIC:
//  Left ON  + Right ON  → straight
//  Left ON  + Right OFF → drifting right → slow right motor
//  Left OFF + Right ON  → drifting left  → slow left motor
//  Left OFF + Right OFF → lost line      → stop
// ════════════════════════════════════════════════════════════════

#include <HTTPClient.h>
#include <WiFi.h>
#include <esp_now.h>

// ⚠️ Local IP from Laptop's Wireless LAN adapter
const char *serverUrl = "http://10.38.236.34:3000/api/telemetry";
unsigned long lastHttpTime = 0;

// ── Motor pins ───────────────────────────────────────────────────
#define PWMA 25
#define AIN1 26
#define AIN2 27
#define PWMB 32
#define BIN1 33
#define BIN2 13
#define STBY 15

// ── PWM setup ────────────────────────────────────────────────────
#define PWM_FREQ 1000
#define PWM_RES 8 // 8-bit: 0–255

// ── Speeds — tune these for your motors ─────────────────────────
#define SPEED_STRAIGHT 180 // both motors, going straight
#define SPEED_OUTER                                                            \
  200 // faster wheel on a turn (bumped up to sweep through curves)
#define SPEED_INNER 30 // slower wheel on a turn (lowered to pivot tight curves)

// ── Shared struct — must match ESP32 #1 ─────────────────────────
typedef struct {
  bool irLeft;
  bool irRight;
} IRPacket;

IRPacket rxData;
bool newData = false;
unsigned long lastRecvTime = 0;
unsigned long lastLineDetectTime =
    0; // Tracks when we last saw the line for gaps

// ── Motor helpers ────────────────────────────────────────────────
void motorA(int speed, bool fwd) {
  digitalWrite(AIN1, fwd ? HIGH : LOW);
  digitalWrite(AIN2, fwd ? LOW : HIGH);
  ledcWrite(PWMA, constrain(speed, 0, 255));
}

void motorB(int speed, bool fwd) {
  digitalWrite(BIN1, fwd ? HIGH : LOW);
  digitalWrite(BIN2, fwd ? LOW : HIGH);
  ledcWrite(PWMB, constrain(speed, 0, 255));
}

void goStraight() {
  motorA(SPEED_STRAIGHT, true);
  motorB(SPEED_STRAIGHT, true);
}

void turnLeft() {
  // Left motor slower, right motor faster
  motorA(SPEED_INNER, true);
  motorB(SPEED_OUTER, true);
}

void turnRight() {
  // Right motor slower, left motor faster
  motorA(SPEED_OUTER, true);
  motorB(SPEED_INNER, true);
}

void stopMotors() {
  ledcWrite(PWMA, 0);
  ledcWrite(PWMB, 0);
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, LOW);
  digitalWrite(BIN1, LOW);
  digitalWrite(BIN2, LOW);
}

// ── ESP-NOW receive callback ─────────────────────────────────────
void onReceive(const esp_now_recv_info_t *info, const uint8_t *data, int len) {
  if (len == sizeof(IRPacket)) {
    memcpy(&rxData, data, sizeof(IRPacket));
    newData = true;
    lastRecvTime = millis();
  }
}

// ── Setup ────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println("\nSafari Bot — ESP32 #2 Line Follow Test");

  // Motor pins
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);
  pinMode(STBY, OUTPUT);
  digitalWrite(STBY, HIGH); // enable driver

  // PWM
  ledcAttach(PWMA, PWM_FREQ, PWM_RES);
  ledcAttach(PWMB, PWM_FREQ, PWM_RES);
  stopMotors();

  // Sync to Hotspot so ESP-NOW matches ESP1 and we can use HTTP requests
  WiFi.mode(WIFI_STA);
  WiFi.begin("Devansh", "dev182005");
  Serial.print("Connecting to Wi-Fi to sync radio channel.");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi Connected! Radio Channel Synced.");

  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW init failed!");
    return;
  }
  esp_now_register_recv_cb(onReceive);

  Serial.println("Waiting for Broadcast IR data from ESP32 #1...");
}

// ── Loop ─────────────────────────────────────────────────────────
void loop() {
  // ── Safety Timeout: Stop motors if disconnected ──
  if (millis() - lastRecvTime > 500) {
    stopMotors();
    Serial.println(">> WAITING FOR CONNECTION...");
    delay(200); // Prevent spamming
    return;
  }

  if (!newData)
    return;
  newData = false;

  bool L = rxData.irLeft;
  bool R = rxData.irRight;

  // Update memory of when we last saw the black line
  if (L || R) {
    lastLineDetectTime = millis();
  }

  if (L && R) {
    goStraight();
    Serial.println(">> STRAIGHT");
  } else if (L && !R) {
    turnLeft();
    Serial.println(">> TURN LEFT  (drifted right)");
  } else if (!L && R) {
    turnRight();
    Serial.println(">> TURN RIGHT (drifted left)");
  } else {
    // !L && !R means we lost the line OR we hit a short gap.
    // To handle short gaps, we keep doing whatever we were doing for 400
    // milliseconds.
    if (millis() - lastLineDetectTime < 400) {
      Serial.println(">> IN GAP: Coasting over the gap...");
    } else {
      // If it's been more than 400ms, the run is actually over.
      stopMotors();
      Serial.println(">> STOP (lost line completely)");
    }
  }

  // ── Send telemetry to Laptop (Non-Blocking: Once every 1000ms) ──
  if (WiFi.status() == WL_CONNECTED && millis() - lastHttpTime > 1000) {
    lastHttpTime = millis();
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    // Send a JSON object matching what server.js /api/telemetry expects
    // We send vehicle speed to the dashboard. You could also dynamically adjust
    // this based on tight curves.
    String jsonPayload =
        "{\"speed\": " + String(SPEED_STRAIGHT) + ", \"position\": 50}";

    int httpResponseCode = http.POST(jsonPayload);
    if (httpResponseCode > 0) {
      Serial.println(">> Dashboard Updated => HTTP: " +
                     String(httpResponseCode));
    }
    http.end();
  }
}
