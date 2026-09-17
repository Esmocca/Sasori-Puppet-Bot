#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pca;

#define SERVO_MOUTH  0
#define SERVO_PITCH  1
#define SERVO_YAW    2
#define SERVO_ARM    3
#define SERVO_THUMB  4

// ===== PCA9685 =====
#define SERVOMIN 150
#define SERVOMAX 600

// ===== SERVO LIMIT =====
#define YAW_RIGHT_MIN 45
#define YAW_CENTER    70
#define YAW_LEFT_MAX  120

#define PITCH_MIN 0
#define PITCH_MAX 20

#define MOUTH_MIN 0
#define MOUTH_MAX 20

#define ARM_MIN 30
#define ARM_MAX 120

#define THUMB_MIN 30
#define THUMB_MAX 100

// ===== CURRENT POSITION =====
int yawPos   = 90;
int pitchPos = 10;
int mouthPos = 0;
int armPos   = 90;
int thumbPos = 90;

// ===== YAW CONTROL =====
// -1 = kanan, 1 = kiri
int currentSide = 0;
int sideCount   = 0;

// =========================

int angleToPulse(int angle)
{
  return map(angle, 0, 180, SERVOMIN, SERVOMAX);
}

void servoWrite(uint8_t ch, int angle)
{
  angle = constrain(angle, 0, 180);
  pca.setPWM(ch, 0, angleToPulse(angle));
}

void applyPose()
{
  servoWrite(SERVO_YAW, yawPos);
  servoWrite(SERVO_PITCH, pitchPos);
  servoWrite(SERVO_MOUTH, mouthPos);
  servoWrite(SERVO_ARM, armPos);
  servoWrite(SERVO_THUMB, thumbPos);
}

void initPose()
{
  yawPos   = 90;
  pitchPos = 10;
  mouthPos = 0;
  armPos   = 90;
  thumbPos = 90;

  applyPose();
}

void printPosition()
{
  Serial.print("Y:");
  Serial.print(yawPos);

  Serial.print(" P:");
  Serial.print(pitchPos);

  Serial.print(" M:");
  Serial.print(mouthPos);

  Serial.print(" A:");
  Serial.print(armPos);

  Serial.print(" T:");
  Serial.println(thumbPos);
}

// =========================
// YAW RANDOM BALANCED
// =========================

void updateYaw()
{
  int nextYaw;

  // Sudah 2x di kiri
  if (currentSide == 1 && sideCount >= 2)
  {
    nextYaw = random(YAW_RIGHT_MIN, YAW_CENTER);

    currentSide = -1;
    sideCount = 1;
  }

  // Sudah 2x di kanan
  else if (currentSide == -1 && sideCount >= 2)
  {
    nextYaw = random(YAW_CENTER + 1, YAW_LEFT_MAX + 1);

    currentSide = 1;
    sideCount = 1;
  }

  // Random normal
  else
  {
    if (random(2))
    {
      // kiri (>90)
      nextYaw = random(YAW_CENTER + 1, YAW_LEFT_MAX + 1);

      if (currentSide == 1)
        sideCount++;
      else
      {
        currentSide = 1;
        sideCount = 1;
      }
    }
    else
    {
      // kanan (<90)
      nextYaw = random(YAW_RIGHT_MIN, YAW_CENTER);

      if (currentSide == -1)
        sideCount++;
      else
      {
        currentSide = -1;
        sideCount = 1;
      }
    }
  }

  yawPos = nextYaw;
}

// =========================
// DEMO
// =========================

void randomDemo()
{
  updateYaw();

  pitchPos = random(PITCH_MIN, PITCH_MAX + 1);
  mouthPos = random(2) ? 20 : 0;

  int armMove = random(10, 16);
  if (random(2))
    armMove *= -1;

  armPos = constrain(
    armPos + armMove,
    ARM_MIN,
    ARM_MAX
  );

  thumbPos = constrain(
    thumbPos + armMove / 2,
    THUMB_MIN,
    THUMB_MAX
  );

  applyPose();
  printPosition();

  delay(random(800, 1500));
}

// =========================

void setup()
{
  Serial.begin(115200);

  pca.begin();
  pca.setPWMFreq(50);

  randomSeed(analogRead(A0));

  initPose();
  printPosition();
}

void loop()
{
  randomDemo();
}
