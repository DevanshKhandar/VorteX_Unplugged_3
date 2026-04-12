// ============================================================
//  VorteX Safari — ESP32-CAM: Vision & Object Detection
//  Color-based animal detection + HTTP POST
//  UNPLUGGED Round 3
// ============================================================

#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_camera.h"

// ── WiFi Config ──────────────────────────────────────────
const char* WIFI_SSID     = "VorteX_Safari";
const char* WIFI_PASSWORD = "hackathon2026";
const char* SERVER_IP     = "192.168.1.100";
const int   SERVER_PORT   = 3000;

// ── Camera Pins (AI-THINKER ESP32-CAM) ───────────────────
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// Flash LED
#define FLASH_LED_PIN      4

// ── Detection Config ─────────────────────────────────────
// Color-based detection: assign colored markers to animals
// Red    → Lion       (Hue ~0-15, 345-360)
// Green  → Elephant   (Hue ~90-150)
// Blue   → Giraffe    (Hue ~200-260)
// Yellow → Rhinoceros (Hue ~45-70)

struct AnimalColor {
  const char* label;
  uint8_t hMin, hMax;    // Hue range (0-179 in OpenCV scale → 0-255 for us)
  uint8_t sMin;          // Min saturation
  uint8_t vMin;          // Min value/brightness
};

const AnimalColor ANIMALS[] = {
  {"lion",       0,   25,  100, 80},    // Red/orange
  {"elephant",   90,  140, 80,  60},    // Green
  {"giraffe",    160, 220, 80,  60},    // Blue
  {"rhinoceros", 35,  65,  100, 80},    // Yellow
};
const int NUM_ANIMALS = 4;

// Detection suppression (avoid duplicates)
unsigned long lastDetectionTime[4] = {0, 0, 0, 0};
const int SUPPRESSION_MS = 8000;  // 8 seconds between same animal

// Capture interval
const int CAPTURE_INTERVAL = 2000;  // 2 seconds
unsigned long lastCapture = 0;

// Track position estimate (receives from serial or estimates)
float estimatedPosition = 0;

// ── Setup ────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println("\n👁️ VorteX Safari — Vision Node");

  // Flash LED
  pinMode(FLASH_LED_PIN, OUTPUT);
  digitalWrite(FLASH_LED_PIN, LOW);

  // Init camera
  initCamera();

  // Connect WiFi
  connectWiFi();

  Serial.println("✅ Vision Node ready — detecting animals every 2s");
}

// ── Main Loop ────────────────────────────────────────────
void loop() {
  if (millis() - lastCapture < CAPTURE_INTERVAL) {
    delay(50);
    return;
  }
  lastCapture = millis();

  // Increment position estimate
  estimatedPosition += 0.5;
  if (estimatedPosition > 100) estimatedPosition = 100;

  // Capture frame
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("⚠️ Camera capture failed");
    return;
  }

  // Analyze the frame for colored objects
  analyzeFrame(fb);

  esp_camera_fb_return(fb);
}

// ── Frame Analysis (Color Detection) ─────────────────────
void analyzeFrame(camera_fb_t* fb) {
  // For RGB565 frames, we scan pixels for dominant colors
  // Frame format: RGB565 at 160x120

  if (fb->format != PIXFORMAT_RGB565) {
    Serial.println("⚠️ Unexpected pixel format");
    return;
  }

  uint16_t* pixels = (uint16_t*)fb->buf;
  int width  = fb->width;
  int height = fb->height;
  int totalPixels = width * height;

  // Count pixels matching each animal's color
  int colorCounts[NUM_ANIMALS] = {0};
  int minBlobPixels = totalPixels / 40;  // Need at least 2.5% of frame

  // Sample every 2nd pixel for speed
  for (int i = 0; i < totalPixels; i += 2) {
    uint16_t pixel = pixels[i];

    // Extract RGB from RGB565
    uint8_t r = ((pixel >> 11) & 0x1F) << 3;
    uint8_t g = ((pixel >> 5)  & 0x3F) << 2;
    uint8_t b = (pixel & 0x1F) << 3;

    // Convert to HSV (simplified)
    uint8_t h, s, v;
    rgb2hsv(r, g, b, &h, &s, &v);

    // Check against each animal's color profile
    for (int a = 0; a < NUM_ANIMALS; a++) {
      bool hueMatch;
      if (ANIMALS[a].hMin <= ANIMALS[a].hMax) {
        hueMatch = (h >= ANIMALS[a].hMin && h <= ANIMALS[a].hMax);
      } else {
        // Wraps around (e.g., red: 345-15)
        hueMatch = (h >= ANIMALS[a].hMin || h <= ANIMALS[a].hMax);
      }

      if (hueMatch &&
          s >= ANIMALS[a].sMin &&
          v >= ANIMALS[a].vMin) {
        colorCounts[a]++;
      }
    }
  }

  // Find the best matching animal
  int bestIdx = -1;
  int bestCount = 0;

  for (int a = 0; a < NUM_ANIMALS; a++) {
    if (colorCounts[a] > minBlobPixels && colorCounts[a] > bestCount) {
      // Check suppression window
      if (millis() - lastDetectionTime[a] > SUPPRESSION_MS) {
        bestIdx = a;
        bestCount = colorCounts[a];
      }
    }
  }

  if (bestIdx >= 0) {
    float confidence = min((float)bestCount / (totalPixels / 2) * 200, 99.0f);
    Serial.printf("🐾 DETECTED: %s (confidence: %.0f%%, pixels: %d)\n",
                  ANIMALS[bestIdx].label, confidence, bestCount);

    // Update suppression timer
    lastDetectionTime[bestIdx] = millis();

    // Flash LED briefly to indicate detection
    digitalWrite(FLASH_LED_PIN, HIGH);
    delay(100);
    digitalWrite(FLASH_LED_PIN, LOW);

    // Send to server
    sendDetection(ANIMALS[bestIdx].label, (int)confidence);
  }
}

// ── RGB to HSV (0-255 scale) ─────────────────────────────
void rgb2hsv(uint8_t r, uint8_t g, uint8_t b,
             uint8_t* h, uint8_t* s, uint8_t* v) {
  uint8_t maxC = max(max(r, g), b);
  uint8_t minC = min(min(r, g), b);
  uint8_t delta = maxC - minC;

  *v = maxC;

  if (maxC == 0) {
    *s = 0;
    *h = 0;
    return;
  }

  *s = (uint8_t)((long)delta * 255 / maxC);

  if (delta == 0) {
    *h = 0;
    return;
  }

  int hue;
  if (maxC == r) {
    hue = 43 * (int)(g - b) / delta;
  } else if (maxC == g) {
    hue = 85 + 43 * (int)(b - r) / delta;
  } else {
    hue = 171 + 43 * (int)(r - g) / delta;
  }

  if (hue < 0) hue += 256;
  *h = (uint8_t)hue;
}

// ── Camera Init ──────────────────────────────────────────
void initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_RGB565;  // For color analysis

  // Low resolution for speed
  config.frame_size   = FRAMESIZE_QQVGA;   // 160x120
  config.jpeg_quality = 12;
  config.fb_count     = 1;
  config.grab_mode    = CAMERA_GRAB_LATEST;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Camera init failed: 0x%x\n", err);
    // Continue without camera — won't crash the system
    return;
  }

  // Adjust sensor settings for better color detection
  sensor_t* sensor = esp_camera_sensor_get();
  if (sensor) {
    sensor->set_brightness(sensor, 1);
    sensor->set_contrast(sensor, 1);
    sensor->set_saturation(sensor, 2);  // Boost saturation for color detection
    sensor->set_whitebal(sensor, 1);
    sensor->set_awb_gain(sensor, 1);
  }

  Serial.println("📷 Camera initialized (160x120 RGB565)");
}

// ── Send Detection to Server ─────────────────────────────
void sendDetection(const char* label, int confidence) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("⚠️ WiFi not connected — detection not sent");
    return;
  }

  HTTPClient http;
  String url = "http://" + String(SERVER_IP) + ":" + String(SERVER_PORT) + "/api/detection";
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  String payload = "{";
  payload += "\"label\":\"" + String(label) + "\",";
  payload += "\"confidence\":" + String(confidence) + ",";
  payload += "\"position\":" + String(estimatedPosition, 1);
  payload += "}";

  int code = http.POST(payload);
  if (code == 200) {
    Serial.println("✅ Detection sent to server");
  } else {
    Serial.printf("⚠️ Detection POST failed: %d\n", code);
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
  } else {
    Serial.println("\n⚠️ WiFi failed — camera will detect but not report");
  }
}

// ============================================================
// 💡 TFLite UPGRADE PATH:
//
// To switch from color-based to ML-based detection:
// 1. Train a model on Edge Impulse (edgeimpulse.com)
//    - Use FOMO (object detection) with 96x96 input
//    - Classes: lion, elephant, giraffe, rhinoceros
//    - Export as Arduino Library
// 2. Include the library and replace analyzeFrame():
//    - Capture frame as RGB888 or JPEG
//    - Run inference using ei_run_classifier()
//    - Extract bounding boxes + labels
//    - Call sendDetection() with results
//
// The color-based approach below works great for hackathon
// demos with colored figurines or stickers on animals.
// ============================================================
