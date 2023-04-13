void setup() {
  Serial.begin(9600); // Initialize Serial Monitor
  pinMode(2, INPUT);  // Set pin 2 as input
}

void loop() {
  if (digitalRead(2) == LOW) { // Check if input on pin 2 is HIGH
    Serial.println("LOW");    // Print "Hello" to Serial Monitor
    delay(100);                // Wait for 1 second before checking input again
  }
  
}