void setup() {
  Serial.begin(9600); // Initialize Serial Monitor
  pinMode(2, INPUT);  // Set pin 2 as input
}

void loop() {
  if (digitalRead(2) == LOW) { // Check if input on pin 2 is HIGH
    Serial.write(1);    // Print "Hello" to Serial Monitor
  } else {
    Serial.write(0);
  }
}