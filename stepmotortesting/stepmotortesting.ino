//yuh
const int stepPin1 = 3;
const int dirPin1 = 4;

const int stepPin2 = 5;
const int dirPin2 = 6;

void setup() {
  // put your setup code here, to run once:
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
}

void loop() {
  digitalWrite(dirPin1, HIGH);
  digitalWrite(dirPin2, HIGH);
  for(int x = 0; x < 100; x++){
    digitalWrite(stepPin1, HIGH);
    delayMicroseconds(500);
    digitalWrite(stepPin1, LOW);
    delayMicroseconds(500);
    digitalWrite(stepPin2, HIGH);
    delayMicroseconds(500);
    digitalWrite(stepPin2, LOW);
    delayMicroseconds(500);
    delay(500);
  }
  delay(500);

  digitalWrite(dirPin1, LOW);
  digitalWrite(dirPin2, LOW);
  for(int x = 0; x < 100; x++){
    digitalWrite(stepPin1, HIGH);
    delayMicroseconds(500);
    digitalWrite(stepPin1, LOW);
    delayMicroseconds(500);
    digitalWrite(stepPin2, HIGH);
    delayMicroseconds(500);
    digitalWrite(stepPin2, LOW);
    delayMicroseconds(500);
    delay(500);
  }
  delay(500);

  // put your main code here, to run repeatedly:
  // digitalWrite(dirPin1, HIGH);

  // for(int x = 0; x < 200; x++){
  //   digitalWrite(stepPin1, HIGH);
  //   delayMicroseconds(500);
  //   digitalWrite(stepPin1, LOW);
  //   delayMicroseconds(500);
  // }
  // delay(500);

  // // digitalWrite(dirPin2, HIGH);

  // for(int x = 0; x < 200; x++){
  //   digitalWrite(stepPin2, HIGH);
  //   delayMicroseconds(500);
  //   digitalWrite(stepPin2, LOW);
  //   delayMicroseconds(500);
  // }
  // delay(500);

  // digitalWrite(dirPin1, LOW);

  // for(int x = 0; x < 400; x++){
  //   digitalWrite(stepPin1, HIGH);
  //   delayMicroseconds(500);
  //   digitalWrite(stepPin1, LOW);
  //   delayMicroseconds(500);
  // }
  // delay(500);

  // digitalWrite(dirPin2, LOW);

  // for(int x = 0; x < 400; x++){
  //   digitalWrite(stepPin2, HIGH);
  //   delayMicroseconds(500);
  //   digitalWrite(stepPin2, LOW);
  //   delayMicroseconds(500);
  // }
  // delay(500);

  // digitalWrite(dirPin1, HIGH);

  // for(int x = 0; x < 200; x++){
  //   digitalWrite(stepPin1, HIGH);
  //   delayMicroseconds(500);
  //   digitalWrite(stepPin1, LOW);
  //   delayMicroseconds(500);
  //   delay(100);
  // }
  // delay(500);

  // digitalWrite(dirPin1, LOW);

  // for(int x = 0; x < 200; x++){
  //   digitalWrite(stepPin1, HIGH);
  //   delayMicroseconds(500);
  //   digitalWrite(stepPin1, LOW);
  //   delayMicroseconds(500);
  //   delay(100);
  // }

  //   digitalWrite(dirPin2, HIGH);

  // for(int x = 0; x < 200; x++){
  //   digitalWrite(stepPin2, HIGH);
  //   delayMicroseconds(500);
  //   digitalWrite(stepPin2, LOW);
  //   delayMicroseconds(500);
  //   delay(100);
  // }
  // delay(500);

  // digitalWrite(dirPin2, LOW);

  // for(int x = 0; x < 200; x++){
  //   digitalWrite(stepPin2, HIGH);
  //   delayMicroseconds(500);
  //   digitalWrite(stepPin2, LOW);
  //   delayMicroseconds(500);
  //   delay(100);
  // }
  //delay(500);
}
