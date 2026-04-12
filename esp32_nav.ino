// ============================================================
//  VorteX Safari — ESP32 #1: Navigation Controller
//  PID Line-Following + WiFi Telemetry
//  UNPLUGGED Round 3
// ============================================================

#include <WiFi.h>
#include <HTTPClient.h>

// ── WiFi Config ──────────────────────────────────────────
// ⚠️ CHANGE THESE to match your network
const char* WIFI_SSID     = "VorteX_Safari";
const char* WIFI_PASSWORD = "hackathon2026";
const char* SERVER_IP     = "192.168.1.100";  // Your laptop's IP
const int   SERVER_PORT   = 3000;

// ── Motor Driver Pins (TB6612FNG) ────────────────────────
#define PWMA  25    // Left motor speed
#define AIN1  26    // Left motor direction
#define AIN2  27
#define PWMB  14    // Right motor speed
#define BIN1  12    // Right motor direction
#define BIN2  13
#define STBY  23    // Standby — must be HIGH

// ── IR Sensor Pins ───────────────────────────────────────
// Using 5 IR sensors for accurate PID
// If you have fewer, set NUM_SENSORS accordingly
#define NUM_SENSORS 5
const int IR_PINS[NUM_SENSORS] = {36, 39, 34, 35, 32};
// Weights: leftmost = -2, center = 0, rightmost = +2
const float WEIGHTS[NUM_SENSORS] = {-2.0, -1.0, 0.0, 1.0, 2.0};

// If you only have 1 IR sensor, set this to 1 and use pin 34
// #define NUM_SENSORS 1
// const int IR_PINS[1] = {34};

// ── PID Parameters ───────────────────────────────────────
// ⚠️ TUNE THESE on the actual track
float Kp = 25.0;
float Ki = 0.0;
float Kd = 18.0;

int   BASE_SPEED   = 150;   // PWM 0-255
int   MAX_SPEED    = 230;
int   MIN_SPEED    = 0;
int   IR_THRESHOLD = 2000;  // ADC threshold for black line (tune!)

float lastError  = 0;
float integral   = 0;

// ── Telemetry ────────────────────────────────────────────
unsigned long lastTelemetry = 0;
const int TELEMETRY_INTERVAL = 500;  // ms
float trackProgress = 0;             // 0-100 estimated position

// ── PWM Config ───────────────────────────────────────────
#define PWM_FREQ     5000
#define PWM_RES      8
#define PWM_CH_A     0
#define PWM_CH_B     1

// ── Setup ────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println("\n🦁 VorteX Safari — Navigation Controller");

  // Motor pins
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT);
  pinMode(BIN2, OUTPUT);
  pinMode(STBY, OUTPUT);
  digitalWrite(STBY, HIGH);

  // PWM channels
  ledcAttach(PWMA, PWM_FREQ, PWM_RES);
  ledcAttach(PWMB, PWM_FREQ, PWM_RES);

  // IR sensor pins
  for (int i = 0; i < NUM_SENSORS; i++) {
    pinMode(IR_PINS[i], INPUT);
  }

  // Stop motors initially
  stopMotors();

  // Connect WiFi
  connectWiFi();

  Serial.println("✅ Navigation Controller ready");
  Serial.printf("   PID: Kp=%.1f  Ki=%.1f  Kd=%.1f\n", Kp, Ki, Kd);
  Serial.printf("   Base speed: %d  Max: %d\n", BASE_SPEED, MAX_SPEED);
}

// ── Main Loop ────────────────────────────────────────────
void loop() {
  // 1. Read IR sensors and compute error
  float error = readLineSensors();

  // 2. PID calculation
  float correction = pidCompute(error);

  // 3. Apply motor speeds
  int leftSpeed  = constrain(BASE_SPEED + correction, MIN_SPEED, MAX_SPEED);
  int rightSpeed = constrain(BASE_SPEED - correction, MIN_SPEED, MAX_SPEED);
  setMotors(leftSpeed, rightSpeed);

  // 4. Update track progress estimate
  // Simple estimation: increment based on speed and direction
  if (leftSpeed > 0 || rightSpeed > 0) {
    trackProgress += 0.02;  // Tune this based on actual track length
    if (trackProgress > 100) trackProgress = 100;
  }

  // 5. Send telemetry periodically
  if (millis() - lastTelemetry > TELEMETRY_INTERVAL) {
    sendTelemetry(leftSpeed, rightSpeed, error);
    lastTelemetry = millis();
  }

  // 6. Debug output
  Serial.printf("ERR:%.2f COR:%.1f L:%d R:%d POS:%.1f%%\n",
                error, correction, leftSpeed, rightSpeed, trackProgress);

  delay(10);  // ~100Hz control loop
}

// ── IR Sensor Reading ────────────────────────────────────
float readLineSensors() {
  if (NUM_SENSORS == 1) {
    // Single sensor: bang-bang control
    int val = analogRead(IR_PINS[0]);
    return (val > IR_THRESHOLD) ? 0.0 : 1.0;  // On line vs off line
  }

  // Multi-sensor weighted average
  float weightedSum = 0;
  float totalActive = 0;

  for (int i = 0; i < NUM_SENSORS; i++) {
    int raw = analogRead(IR_PINS[i]);
    float active = (raw > IR_THRESHOLD) ? 1.0 : 0.0;

    weightedSum += WEIGHTS[i] * active;
    totalActive += active;
  }

  if (totalActive == 0) {
    // Line lost — use last known direction
    return (lastError > 0) ? 2.5 : -2.5;
  }

  return weightedSum / totalActive;
}

// ── PID Controller ───────────────────────────────────────
float pidCompute(float error) {
  float derivative = error - lastError;
  integral += error;
  integral = constrain(integral, -50, 50);  // Anti-windup

  float output = (Kp * error) + (Ki * integral) + (Kd * derivative);
  lastError = error;

  return output;
}

// ── Motor Control ────────────────────────────────────────
void setMotors(int left, int right) {
  // Left motor (A)
  if (left >= 0) {
    digitalWrite(AIN1, HIGH);
    digitalWrite(AIN2, LOW);
  } else {
    digitalWrite(AIN1, LOW);
    digitalWrite(AIN2, HIGH);
    left = -left;
  }
  ledcWrite(PWMA, left);

  // Right motor (B)
  if (right >= 0) {
    digitalWrite(BIN1, HIGH);
    digitalWrite(BIN2, LOW);
  } else {
    digitalWrite(BIN1, LOW);
    digitalWrite(BIN2, HIGH);
    right = -right;
  }
  ledcWrite(PWMB, right);
}

void stopMotors() {
  ledcWrite(PWMA, 0);
  ledcWrite(PWMB, 0);
}

// ── WiFi ─────────────────────────────────────────────────
void connectWiFi() {
  Serial.printf("📶 Connecting to %s", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int retries = 0;
  while (WiFi.status() != WL_CONNECTED && retries < 40) {
    delay(500);
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n✅ WiFi connected! IP: %s\n", WiFi.localIP().toString().c_str());
  } else {
    Serial.println("\n⚠️ WiFi failed — running offline (no telemetry)");
  }
}

// ── Telemetry POST ───────────────────────────────────────
void sendTelemetry(int leftSpeed, int rightSpeed, float error) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + "/api/telemetry";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  float avgSpeed = (leftSpeed + rightSpeed) / 2.0;
  String payload = "{";
  payload += "\"position\":" + String(trackProgress, 1) + ",";
  payload += "\"speed\":"    + String(avgSpeed, 1) + ",";
  payload += "\"error\":"    + String(error, 2);
  payload += "}";

  int code = http.POST(payload);
  if (code != 200) {
    Serial.printf("⚠️ Telemetry POST failed: %d\n", code);
  }
  http.end();
}
