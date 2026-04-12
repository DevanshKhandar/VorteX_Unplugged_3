// ============================================================
//  VorteX Safari — ESP32 #2: Telemetry Hub
//  RFID (MFRC522) + GPS (TinyGPS++) + AQI Sensor
//  UNPLUGGED Round 3
// ============================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <TinyGPSPlus.h>
#include <HardwareSerial.h>

// ── WiFi Config ──────────────────────────────────────────
const char* WIFI_SSID     = "VorteX_Safari";
const char* WIFI_PASSWORD = "hackathon2026";
const char* SERVER_IP     = "192.168.1.100";
const int   SERVER_PORT   = 3000;

// ── RFID Pins (MFRC522 on SPI) ──────────────────────────
#define RFID_SS   5     // SDA / CS
#define RFID_RST  22
// SPI defaults: SCK=18, MOSI=23, MISO=19

// ── GPS Pins (on UART2) ─────────────────────────────────
#define GPS_RX  16      // ESP32 RX ← GPS TX
#define GPS_TX  17      // ESP32 TX → GPS RX
#define GPS_BAUD 9600

// ── AQI Sensor Pin ───────────────────────────────────────
#define AQI_PIN 34      // Analog input

// ── LED ──────────────────────────────────────────────────
#define LED_PIN 2       // Built-in LED for status

// ── Objects ──────────────────────────────────────────────
MFRC522 rfid(RFID_SS, RFID_RST);
TinyGPSPlus gps;
HardwareSerial gpsSerial(2);  // UART2

// ── State ────────────────────────────────────────────────
bool runActive  = false;
bool rfidTriggered = false;
unsigned long lastTelemetry = 0;
const int TELEMETRY_INTERVAL = 1000;  // 1 second

// RFID suppression
unsigned long lastRfidRead = 0;
const int RFID_COOLDOWN = 5000;  // 5 seconds

// ── Setup ────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println("\n📡 VorteX Safari — Telemetry Hub");

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // SPI for RFID
  SPI.begin();
  rfid.PCD_Init();
  delay(100);

  // Check RFID reader
  byte ver = rfid.PCD_ReadRegister(rfid.VersionReg);
  if (ver == 0x00 || ver == 0xFF) {
    Serial.println("⚠️ RFID reader not detected — check wiring!");
  } else {
    Serial.printf("✅ RFID reader detected (version 0x%02X)\n", ver);
  }

  // GPS Serial
  gpsSerial.begin(GPS_BAUD, SERIAL_8N1, GPS_RX, GPS_TX);
  Serial.println("✅ GPS serial started on UART2");

  // AQI sensor
  pinMode(AQI_PIN, INPUT);
  Serial.println("✅ AQI sensor on GPIO " + String(AQI_PIN));

  // WiFi
  connectWiFi();

  Serial.println("✅ Telemetry Hub ready");
  Serial.println("   Waiting for RFID tag, GPS fix, and AQI data...");
}

// ── Main Loop ────────────────────────────────────────────
void loop() {
  // 1. Check RFID
  checkRFID();

  // 2. Read GPS
  readGPS();

  // 3. Send periodic telemetry (GPS + AQI)
  if (millis() - lastTelemetry > TELEMETRY_INTERVAL) {
    sendTelemetry();
    lastTelemetry = millis();
  }

  delay(50);
}

// ── RFID Check ───────────────────────────────────────────
void checkRFID() {
  // Don't re-trigger within cooldown
  if (millis() - lastRfidRead < RFID_COOLDOWN) return;

  // Check for new card
  if (!rfid.PICC_IsNewCardPresent()) return;
  if (!rfid.PICC_ReadCardSerial()) return;

  // Read UID
  String tagId = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (i > 0) tagId += ":";
    if (rfid.uid.uidByte[i] < 0x10) tagId += "0";
    tagId += String(rfid.uid.uidByte[i], HEX);
  }
  tagId.toUpperCase();

  Serial.printf("🏷️ RFID Tag detected: %s\n", tagId.c_str());

  lastRfidRead = millis();

  // Blink LED
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
    delay(100);
  }

  // Send RFID event to server (end of run)
  sendRFID(tagId);

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}

// ── GPS Read ─────────────────────────────────────────────
void readGPS() {
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }
}

// ── AQI Read ─────────────────────────────────────────────
int readAQI() {
  // Read analog value and convert to AQI estimate
  int raw = analogRead(AQI_PIN);
  // Map 0-4095 ADC to 0-500 AQI scale (tune based on sensor)
  int aqi = map(raw, 0, 4095, 0, 300);
  aqi = constrain(aqi, 0, 500);
  return aqi;
}

// ── Send Telemetry ───────────────────────────────────────
void sendTelemetry() {
  if (WiFi.status() != WL_CONNECTED) return;

  int aqi = readAQI();
  float lat = 0, lng = 0;
  bool hasGps = false;

  if (gps.location.isValid()) {
    lat = gps.location.lat();
    lng = gps.location.lng();
    hasGps = true;
  }

  HTTPClient http;
  String url = "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + "/api/telemetry";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  String payload = "{";
  payload += "\"aqi\":" + String(aqi);
  if (hasGps) {
    payload += ",\"gps\":{\"lat\":" + String(lat, 6) + ",\"lng\":" + String(lng, 6) + "}";
  }
  payload += "}";

  int code = http.POST(payload);
  if (code != 200) {
    Serial.printf("⚠️ Telemetry POST failed: %d\n", code);
  }
  http.end();

  // Debug
  Serial.printf("📊 AQI:%d  GPS:%s (%.4f, %.4f)\n",
                aqi,
                hasGps ? "FIX" : "NO FIX",
                lat, lng);
}

// ── Send RFID Event ──────────────────────────────────────
void sendRFID(String tagId) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi not connected — RFID event not sent");
    return;
  }

  HTTPClient http;
  String url = "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + "/api/rfid";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  String payload = "{\"tagId\":\"" + tagId + "\"}";

  int code = http.POST(payload);
  if (code == 200) {
    Serial.println("✅ RFID event sent — run complete!");
    rfidTriggered = true;
  } else {
    Serial.printf("⚠️ RFID POST failed: %d\n", code);
  }
  http.end();
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
    // Blink LED to confirm
    for (int i = 0; i < 5; i++) {
      digitalWrite(LED_PIN, HIGH);
      delay(50);
      digitalWrite(LED_PIN, LOW);
      delay(50);
    }
  } else {
    Serial.println("\n⚠️ WiFi failed — running offline");
  }
}
