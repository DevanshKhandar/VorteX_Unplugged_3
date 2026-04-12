// ════════════════════════════════════════════════════════════════
//  MANUAL ROVER — ESP32 WEBSERVER
//  Drives TB6612FNG via WiFi GET requests (Joystick/Keys)
// ════════════════════════════════════════════════════════════════

#include <WiFi.h>
#include <WebServer.h>

// ── Motor pins ───────────────────────────────────────────────────
#define PWMA  25
#define AIN1  26
#define AIN2  27
#define PWMB  32
#define BIN1  33
#define BIN2  13
#define STBY  15

// ── PWM setup ────────────────────────────────────────────────────
#define PWM_FREQ   1000
#define PWM_RES    8
#define SPEED_MAX  150  // Reduced to 150 to prevent Battery Voltage Drop (Brownout Reset)

WebServer server(80);

void motorA(int speed, bool fwd) {
  digitalWrite(AIN1, fwd ? HIGH : LOW);
  digitalWrite(AIN2, fwd ? LOW  : HIGH);
  ledcWrite(PWMA, constrain(speed, 0, 255));
}
void motorB(int speed, bool fwd) {
  digitalWrite(BIN1, fwd ? HIGH : LOW);
  digitalWrite(BIN2, fwd ? LOW  : HIGH);
  ledcWrite(PWMB, constrain(speed, 0, 255));
}
void stopMotors() {
  ledcWrite(PWMA, 0); ledcWrite(PWMB, 0);
  digitalWrite(AIN1, LOW); digitalWrite(AIN2, LOW);
  digitalWrite(BIN1, LOW); digitalWrite(BIN2, LOW);
}

// Ensure Web Dashboard can fetch from a different IP (CORS)
void sendCORS() {
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
}
void handleOptions() {
  sendCORS();
  server.send(204);
}

void setup() {
  Serial.begin(115200);
  
  // Motor Init
  pinMode(AIN1, OUTPUT); pinMode(AIN2, OUTPUT);
  pinMode(BIN1, OUTPUT); pinMode(BIN2, OUTPUT);
  pinMode(STBY, OUTPUT); digitalWrite(STBY, HIGH);
  ledcAttach(PWMA, PWM_FREQ, PWM_RES);
  ledcAttach(PWMB, PWM_FREQ, PWM_RES);
  stopMotors();

  // WiFi Init
  WiFi.mode(WIFI_STA);
  WiFi.begin("Devansh", "dev182005");
  Serial.print("\nConnecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\n✅ WiFi Connected!");
  Serial.print("➡️ TYPE THIS IP INTO THE DASHBOARD: ");
  Serial.println(WiFi.localIP());

  // API Routes
  server.on("/", HTTP_OPTIONS, handleOptions);
  server.on("/fwd", HTTP_OPTIONS, handleOptions);
  server.on("/rev", HTTP_OPTIONS, handleOptions);
  server.on("/left", HTTP_OPTIONS, handleOptions);
  server.on("/right", HTTP_OPTIONS, handleOptions);
  server.on("/stop", HTTP_OPTIONS, handleOptions);

  server.on("/fwd", HTTP_GET, [](){ sendCORS(); motorA(SPEED_MAX, true); motorB(SPEED_MAX, true); server.send(200, "text/plain", "OK"); });
  server.on("/rev", HTTP_GET, [](){ sendCORS(); motorA(SPEED_MAX, false); motorB(SPEED_MAX, false); server.send(200, "text/plain", "OK"); });
  
  // Turning handles spinning on the spot (differential steering)
  server.on("/left", HTTP_GET, [](){ sendCORS(); motorA(SPEED_MAX, false); motorB(SPEED_MAX, true); server.send(200, "text/plain", "OK"); });
  server.on("/right", HTTP_GET, [](){ sendCORS(); motorA(SPEED_MAX, true); motorB(SPEED_MAX, false); server.send(200, "text/plain", "OK"); });
  
  server.on("/stop", HTTP_GET, [](){ sendCORS(); stopMotors(); server.send(200, "text/plain", "OK"); });
  
  server.onNotFound([]() { sendCORS(); server.send(404, "text/plain", "404"); });
  server.begin();
}

void loop() {
  server.handleClient();
}
