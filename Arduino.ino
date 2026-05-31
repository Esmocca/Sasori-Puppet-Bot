#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pca = Adafruit_PWMServoDriver();

#define SERVOMIN 150
#define SERVOMAX 600

#define SERVO_MULUT 0
#define SERVO_PITCH 1
#define SERVO_YAW   2

#define BUZZER_PIN 4

int currentYaw   = 90;
int currentPitch = 80;
int currentMouth = 0;

// ======================================
// SERVO
// ======================================

int angleToPulse(int angle)
{
  return map(
    angle,
    0,
    180,
    SERVOMIN,
    SERVOMAX
  );
}

void setServo(
  uint8_t channel,
  int angle
)
{
  angle = constrain(
    angle,
    0,
    180
  );

  if(channel == SERVO_PITCH)
  {
    angle = constrain(
      angle,
      50,
      100
    );
  }

  int pulse =
    angleToPulse(angle);

  pca.setPWM(
    channel,
    0,
    pulse
  );
}

// ======================================
// BUZZER
// ======================================

void beep(
  int freq,
  int duration
)
{
  tone(
    BUZZER_PIN,
    freq,
    duration
  );

  delay(duration);

  noTone(BUZZER_PIN);
}

void bootSuccessTone()
{
  beep(2500, 200);
}

void lowBatteryTone()
{
  for(int i=0;i<3;i++)
  {
    beep(1500,150);
    delay(150);
  }
}

void fullBatteryTone()
{
  tone(BUZZER_PIN, 1319, 90);   // E6
  delay(110);

  tone(BUZZER_PIN, 1568, 90);   // G6
  delay(110);

  tone(BUZZER_PIN, 2093, 180);  // C7
  delay(220);

  noTone(BUZZER_PIN);
}

// ======================================
// APPLY SERVO
// ======================================

void applyServo()
{
  setServo(
    SERVO_YAW,
    currentYaw
  );

  setServo(
    SERVO_PITCH,
    currentPitch
  );

  setServo(
    SERVO_MULUT,
    currentMouth
  );
}

// ======================================
// SETUP
// ======================================

void setup()
{
  Serial.begin(115200);

  pinMode(
    BUZZER_PIN,
    OUTPUT
  );

  digitalWrite(
    BUZZER_PIN,
    LOW
  );

  pca.begin();
  pca.setPWMFreq(50);

  delay(500);

  currentYaw = 90;
  currentPitch = 80;
  currentMouth = 0;

  applyServo();

  delay(1000);
}

// ======================================
// SERIAL COMMAND
// ======================================

void processCommand(
  String cmd
)
{
  cmd.trim();

  // ------------------------
  // BOOT SUCCESS
  // ------------------------
  if(cmd == "BOOT_OK")
  {
    bootSuccessTone();
    return;
  }

  // ------------------------
  // LOW BATTERY
  // ------------------------
  if(cmd == "LOW_BAT")
  {
    lowBatteryTone();
    return;
  }

  // ------------------------
  // FULL BATTERY
  // ------------------------
  if(cmd == "FULL_BAT")
  {
    fullBatteryTone();
    return;
  }

  // ------------------------
  // YAW,PITCH,MOUTH
  // ------------------------

  int p1 = cmd.indexOf(',');
  int p2 = cmd.indexOf(
    ',',
    p1 + 1
  );

  if(
    p1 < 0 ||
    p2 < 0
  )
  {
    return;
  }

  currentYaw =
    cmd.substring(
      0,
      p1
    ).toInt();

  currentPitch =
    cmd.substring(
      p1 + 1,
      p2
    ).toInt();

  currentMouth =
    cmd.substring(
      p2 + 1
    ).toInt();

  currentYaw =
    constrain(
      currentYaw,
      0,
      180
    );

  currentPitch =
    constrain(
      currentPitch,
      50,
      100
    );

  currentMouth =
    constrain(
      currentMouth,
      0,
      60
    );

  applyServo();
}

// ======================================
// LOOP
// ======================================

void loop()
{
  if(
    Serial.available()
  )
  {
    String cmd =
      Serial.readStringUntil(
        '\n'
      );

    processCommand(cmd);
  }
}
