#include <Wire.h>
#include <Adafruit_AHTX0.h>

Adafruit_AHTX0 aht;

int pin3State = HIGH;
int pin4State = HIGH;
int pin5State = HIGH;
int pin6State = HIGH;
int pin7State = HIGH;
int pin8State = HIGH;

int soilMoisturePin1 = A0;  
int soilMoisturePin2 = A1;  

void setup() {
  Serial.begin(115200);  
  Wire.begin();

  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  pinMode(7, OUTPUT);
  pinMode(8, OUTPUT);
  digitalWrite(3, pin3State);
  digitalWrite(4, pin4State);
  digitalWrite(5, pin5State);
  digitalWrite(6, pin6State);
  digitalWrite(7, pin7State);
  digitalWrite(8, pin8State);


  if (!aht.begin()) {
    Serial.println("Couldn't find AHT20 sensor!");
    while (1);  
  }
  
  Serial.println("AHT20 Sensor Initialized.");
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');  
    
    if (command == "GET_DATA") {  
      sensors_event_t humidity, temperature;
      aht.getEvent(&humidity, &temperature);

      int soilMoisture1 = analogRead(soilMoisturePin1);  
      int soilMoisture2 = analogRead(soilMoisturePin2);  

      float soilMoisture1Percentage = map(soilMoisture1, 550, 250, 0, 100);
      float soilMoisture2Percentage = map(soilMoisture2, 550, 250, 0, 100);

soilMoisture1Percentage = constrain(soilMoisture1Percentage, 0, 100);
soilMoisture2Percentage = constrain(soilMoisture2Percentage, 0, 100);

    Serial.println(String(temperature.temperature) + "," + String(humidity.relative_humidity) + "," + String(soilMoisture1Percentage) + "," + String(soilMoisture2Percentage));

    }
    if (command == "TOGGLE_PIN3") {
      pin3State = (pin3State == LOW) ? HIGH : LOW;
      digitalWrite(3, pin3State);
    }
    if (command == "TOGGLE_PIN4") {
      pin4State = (pin4State == LOW) ? HIGH : LOW;
      digitalWrite(4, pin4State);
    }
    if (command == "TOGGLE_PIN5") {
      pin5State = (pin5State == LOW) ? HIGH : LOW;
      digitalWrite(5, pin5State);
    }
    if (command == "TOGGLE_PIN6") {
      pin6State = (pin6State == LOW) ? HIGH : LOW;
      digitalWrite(6, pin6State);
    }
    if (command == "TOGGLE_PIN7") {
      pin7State = (pin7State == LOW) ? HIGH : LOW;
      digitalWrite(7, pin7State);
    }
    if (command == "TOGGLE_PIN8") {
      pin8State = (pin8State == LOW) ? HIGH : LOW;
      digitalWrite(8, pin8State);
    }
  }

  delay(1000); 
}
