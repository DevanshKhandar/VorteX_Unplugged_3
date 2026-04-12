// VORTEX STANDALONE AUTO ROVER (PURE NAVIGATION)
//
// TRACK: WHITE background with BLACK line
// SENSOR LAYOUT: [LEFT_IR] ─── BLACK LINE ─── [RIGHT_IR]
//
// 🟢 IR Sensors
//   - D35 -> LEFT
//   - D12 -> RIGHT
//
// 🔴 Motors (TB6612FNG)
//   - Motor A (D25, D26, D27) -> Left wheel
//   - Motor B (D32, D33, D13) -> Right wheel 
//   - D15 -> STBY

#define PWMA 25
#define AIN1 26
#define AIN2 27
#define PWMB 32
#define BIN1 33
#define BIN2 13
#define STBY 15

#define SL   35
#define SR   12

#define SPEED     150   // Straight-line speed
#define TURN_SPD  170   // Correction speed
#define THRESH    2000  // Analog threshold: above = WHITE (HIGH), below = BLACK (LOW)

// ── Motor helpers ────────────────────────────────────────
// LEFT WHEEL (Motor A)
void lFwd(int s) { digitalWrite(AIN1,HIGH); digitalWrite(AIN2,LOW);  ledcWrite(PWMA,s); }
void lRev(int s) { digitalWrite(AIN1,LOW);  digitalWrite(AIN2,HIGH); ledcWrite(PWMA,s); }
void lOff()      { digitalWrite(AIN1,LOW);  digitalWrite(AIN2,LOW);  ledcWrite(PWMA,0); }

// RIGHT WHEEL (Motor B)
void rFwd(int s) { digitalWrite(BIN1,HIGH); digitalWrite(BIN2,LOW);  ledcWrite(PWMB,s); }
void rRev(int s) { digitalWrite(BIN1,LOW);  digitalWrite(BIN2,HIGH); ledcWrite(PWMB,s); }
void rOff()      { digitalWrite(BIN1,LOW);  digitalWrite(BIN2,LOW);  ledcWrite(PWMB,0); }

void stopAll() { lOff(); rOff(); }

// ── Setup ────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  
  pinMode(AIN1,OUTPUT); pinMode(AIN2,OUTPUT);
  pinMode(BIN1,OUTPUT); pinMode(BIN2,OUTPUT);
  pinMode(STBY,OUTPUT); digitalWrite(STBY,HIGH);
  pinMode(SL,INPUT);    pinMode(SR,INPUT);
  
  ledcAttach(PWMA, 1000, 8);
  ledcAttach(PWMB, 1000, 8);
  stopAll();

  Serial.println("\n=== VORTEX PURE AUTO ROVER ===");
  Serial.println("Wi-Fi removed completely to eliminate stuttering.");
  delay(1000);
}

// ── Main Loop ────────────────────────────────────────────
void loop() {
  int lv = analogRead(SL);
  int rv = analogRead(SR);

  // WHITE background reflects light -> high sensor reading (analog > THRESH)
  // BLACK line absorbs light        -> low sensor reading (analog < THRESH)
  bool L_white = (lv > THRESH);
  bool R_white = (rv > THRESH);

  if (L_white && R_white) {
    // Both sensors on white background → Coasting / Straight
    lFwd(SPEED);
    rFwd(SPEED);
  }
  else if (!L_white && R_white) {
    // Left sensor on black line -> rover drifted RIGHT -> correct LEFT
    lOff();
    rFwd(TURN_SPD);
  }
  else if (L_white && !R_white) {
    // Right sensor on black line -> rover drifted LEFT -> correct RIGHT
    lFwd(TURN_SPD);
    rOff();
  }
  else {
    // Both sensors on black line -> Intersection or Gap
    lFwd(SPEED);
    rFwd(SPEED);
  }
}