#include <SoftwareSerial.h>

SoftwareSerial mySerial(52, 53);

const int trig_1 = 2;
const int echo_1 = 3;

const int trig_2 = 4;
const int echo_2 = 5;

const int trig_3 = 6;
const int echo_3 = 7;

const int trig_4 = 8;
const int echo_4 = 9;

const int trig_5 = 10;
const int echo_5 = 11;

const int trig_6 = 12;
const int echo_6 = 13;

const int haptic_1 = A0;
const int haptic_2 = A1;
const int haptic_3 = A2;
const int haptic_4 = A3;
const int haptic_5 = A4;
const int haptic_6 = A5;


float distanceCM_1 = 0, resultCM_1 = 0;
float distanceCM_2 = 0, resultCM_2 = 0;
float distanceCM_3 = 0, resultCM_3 = 0;
float distanceCM_4 = 0, resultCM_4 = 0;
float distanceCM_5 = 0, resultCM_5 = 0;
float distanceCM_6 = 0, resultCM_6 = 0;


long Time_1, Time_2, Time_3, Time_4, Time_5, Time_6;
float hap_1, hap_2, hap_3, hap_4, hap_5, hap_6;
float Dist_1 = 50.0, Dist_2 = 50.0, Dist_3 = 50.0, Dist_4 = 50.0, Dist_5 = 50.0, Dist_6 = 50.0;
int total = 0, timer_cnt = 0;

void setup()
{
  Serial.begin(9600);
  mySerial.begin(115200);
  pinMode(trig_1, OUTPUT);
  pinMode(trig_2, OUTPUT);
  pinMode(trig_3, OUTPUT);
  pinMode(trig_4, OUTPUT);
  pinMode(trig_5, OUTPUT);
  pinMode(trig_6, OUTPUT);
  

  pinMode(echo_1, INPUT);
  pinMode(echo_2, INPUT);
  pinMode(echo_3, INPUT);
  pinMode(echo_4, INPUT);
  pinMode(echo_5, INPUT);
  pinMode(echo_6, INPUT);
  
  digitalWrite(trig_1, LOW);
  digitalWrite(trig_2, LOW);
  digitalWrite(trig_3, LOW);
  digitalWrite(trig_4, LOW);
  digitalWrite(trig_5, LOW);
  digitalWrite(trig_6, LOW);
  


  pinMode(haptic_1, OUTPUT);
  pinMode(haptic_2, OUTPUT);
  pinMode(haptic_3, OUTPUT);
  pinMode(haptic_4, OUTPUT);
  pinMode(haptic_5, OUTPUT);
  pinMode(haptic_6, OUTPUT);
  
  
}

void loop()
{
  total = 0;
  hap_1 = sensor_1();
  hap_2 = sensor_2();
  hap_3 = sensor_3();
  hap_4 = sensor_4();
  hap_5 = sensor_5();
  hap_6 = sensor_6();
  
  Serial.println("jam 12:");
  if (hap_1 <= Dist_1)
  {
    digitalWrite(haptic_1, HIGH);
    Serial.println("jam 12 ada halangan");
  }
  else
  {
    total += 1;
  }
  if (hap_1 > Dist_1)
  {
    digitalWrite(haptic_1, LOW);
    Serial.println("jam 12 aman");
    // displayParkingFee(1);
  }
  // lcd.setCursor(6, 0);
  Serial.println("jam 11:");
  if (hap_2 <= Dist_2)
  {
    digitalWrite(haptic_2, HIGH);
    Serial.println("jam 11 ada halangan");
  }
  else
  {
    total += 1;
  }
  if (hap_2 > Dist_2)
  {
    digitalWrite(haptic_2, LOW);
    Serial.println("jam 11 aman");
    // displayParkingFee(2);
  }
  // lcd.setCursor(12, 0);
  Serial.println("jam 7:");
  if (hap_3 <= Dist_3)
  {
    digitalWrite(haptic_3, HIGH);
    Serial.println("jam 7 ada halangan");
  }
  else
  {
    total += 1;
  }
  if (hap_3 > Dist_3)
  {
    digitalWrite(haptic_3, LOW);
    Serial.println("jam 7 aman");
    // displayParkingFee(3);
  }
  // lcd.setCursor(18, 0);
  Serial.println("jam 6:");
  if (hap_4 <= Dist_4)
  {
    digitalWrite(haptic_4, HIGH);
    Serial.println("jam 6 ada halangan");
  }
  else
  {
    total += 1;
  }
  if (hap_4 > Dist_4)
  {
    digitalWrite(haptic_4, LOW);
    Serial.println("jam 6 aman");
    // displayParkingFee(4);
  }
  
  Serial.println("jam 5:");
  if (hap_5 <= Dist_5)
  {
    digitalWrite(haptic_5, HIGH);
    Serial.println("jam 5 ada halangan");
  }
  else
  {
    total += 1;
  }
  if (hap_5 > Dist_5)
  {
    digitalWrite(haptic_5, LOW);
    Serial.println("jam 5 aman");
    // displayParkingFee(5);
  }
  // lcd.setCursor(0, 5);
  Serial.println("jam 1:");
  if (hap_6 <= Dist_6)
  {
    digitalWrite(haptic_6, HIGH);
    Serial.println("jam 1 ada halangan");
  }
  else
  {
    total += 1;
  }
  if (hap_6 > Dist_6)
  {
    digitalWrite(haptic_6, LOW);
    Serial.println("jam 1 aman");
    // displayParkingFee(6);
  }
  Serial.print("jam 12: ");
  Serial.print(hap_1);
  Serial.print(" jam 11: ");
  Serial.print(hap_2);
  Serial.print(" jam 7: ");
  Serial.print(hap_3);
  Serial.print(" jam 6: ");
  Serial.print(hap_4);
  Serial.print(" jam 5: ");
  Serial.print(hap_5);
  Serial.print(" jam 1: ");
  Serial.print(hap_6);
  delay(2000);
}

float sensor_1(void)
{
  digitalWrite(trig_1, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig_1, LOW);
  Time_1 = pulseIn(echo_1, HIGH);
  distanceCM_1 = Time_1 * 0.034;
  return resultCM_1 = distanceCM_1 / 2;
}

float sensor_2(void)
{
  digitalWrite(trig_2, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig_2, LOW);
  Time_2 = pulseIn(echo_2, HIGH);
  distanceCM_2 = Time_2 * 0.034;
  return resultCM_2 = distanceCM_2 / 2;
}

float sensor_3(void)
{
  digitalWrite(trig_3, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig_3, LOW);
  Time_3 = pulseIn(echo_3, HIGH);
  distanceCM_3 = Time_3 * 0.034;
  return resultCM_3 = distanceCM_3 / 2;
}

float sensor_4(void)
{
  digitalWrite(trig_4, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig_4, LOW);
  Time_4 = pulseIn(echo_4, HIGH);
  distanceCM_4 = Time_4 * 0.034;
  return resultCM_4 = distanceCM_4 / 2;
}

float sensor_5(void)
{
  digitalWrite(trig_5, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig_5, LOW);
  Time_5 = pulseIn(echo_5, HIGH);
  distanceCM_5 = Time_5 * 0.034;
  return resultCM_5 = distanceCM_5 / 2;
}

float sensor_6(void)
{
  digitalWrite(trig_6, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig_6, LOW);
  Time_6 = pulseIn(echo_6, HIGH);
  distanceCM_6 = Time_6 * 0.034;
  return resultCM_6 = distanceCM_6 / 2;
}

