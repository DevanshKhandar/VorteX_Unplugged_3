// ════════════════════════════════════════════════════════════════
//  LINE FOLLOW TEST — ESP32 #1
//  Reads IR sensors, sends to ESP32 #2 via ESP-NOW
//  D34 = IR Left
//  D35 = IR Right
// ════════════════════════════════════════════════════════════════

#include <WiFi.h>
#include <esp_now.h>

#define IR_LEFT  34
#define IR_RIGHT 35

// ── Broadcast MAC Address ────────────────────────────────────────
// Using Broadcast means you DO NOT need to copy ESP2's MAC address!
// ESP1 will just shout the data out, and ESP2 will listen.
uint8_t broadcastMAC[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

typedef struct {
  bool irLeft;
  bool irRight;
} IRPacket;

IRPacket packet;

void onSent(const uint8_t* mac, esp_now_send_status_t status) {
  // uncomment below to debug sends
  // Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Sent OK" : "Send FAIL");
}

void setup() {
  Serial.begin(115200);
  pinMode(IR_LEFT,  INPUT);
  pinMode(IR_RIGHT, INPUT);

  // Sync Radio Channel to Hotspot so ESP-NOW matches ESP2
  WiFi.mode(WIFI_STA);
  WiFi.begin("Devansh", "dev182005");
  Serial.print("Connecting to Wi-Fi to sync radio channel.");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi Connected! Radio Channel Synced.");

  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW init failed!"); return;
  }
  esp_now_register_send_cb(onSent);

  esp_now_peer_info_t peer = {};
  memcpy(peer.peer_addr, broadcastMAC, 6);
  peer.channel = 0;
  peer.encrypt = false;
  if (esp_now_add_peer(&peer) != ESP_OK) {
    Serial.println("Peer add failed — check MAC!"); return;
  }

  Serial.println("Ready — sending IR data to ESP32 #2");
}

void loop() {
  // LOW = line detected on HW-201
  packet.irLeft  = (digitalRead(IR_LEFT)  == LOW);
  packet.irRight = (digitalRead(IR_RIGHT) == LOW);

  esp_now_send(broadcastMAC, (uint8_t*)&packet, sizeof(packet));

  Serial.printf("IR Left: %s | IR Right: %s\n",
    packet.irLeft  ? "LINE" : "clear",
    packet.irRight ? "LINE" : "clear");

  delay(50); // 20 times per second
}
