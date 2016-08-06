


#include<Stepper.h>
#include<Servo.h>
#include<LiquidCrystal.h>     
#include<NewPing.h>

#define TRIGGER_PIN  6  // Arduino pin tied to trigger pin on the ultrasonic sensor.
#define ECHO_PIN     7  // Arduino pin tied to echo pin on the ultrasonic sensor.
#define MAX_DISTANCE 200 // Maximum distance we want to ping for (in centimeters). Maximum sensor distance is rated at 400-500cm.

//2 3 4 5 6 7 8 9  10 11 12 13  14 23 24 25 26

NewPing sonar(TRIGGER_PIN, ECHO_PIN, MAX_DISTANCE); // NewPing setup of pins and maximum distance.
const int stepsPerRevolution = 200;  // change this to fit the number of steps per revolution
// for your motor

LiquidCrystal lcd(12, 14, 5, 4, 3, 2);
Servo myservo;  // create servo object to control a servo
Stepper myStepper(stepsPerRevolution, 8, 9, 10, 11);

int val;    // variable to read the value from the analog pin


void setup() {
 
    //Servo setup
      myservo.attach(13);  // attaches the servo on pin 9 to the servo object

    //Stepper Setup
      myStepper.setSpeed(60);

    //LCD setup
     lcd.begin(20, 4);
    //BUZZER Setup
    pinMode(53,OUTPUT);
    //INTIALISE INPUT PINS FROM RPI
    pinMode(22,INPUT);
    pinMode(23,INPUT);
    pinMode(24,INPUT);
    pinMode(25,INPUT);
    pinMode(52,OUTPUT);
    //ultrasound setup
    Serial.begin(9600); // Open serial monitor at 115200 baud to see ping results.

}

void loop() {
  if(digitalRead(22)==0){
    //buzzer code
    digitalWrite(53,HIGH);
    delay(3000);
    digitalWrite(53,LOW);
    
    //LCD code
    lcd.setCursor(0, 1);
    lcd.print("Namaste! Medicine time!");
    lcd.setCursor(0, 2);
    lcd.print("Medicine Name");

    //stepper
    for(int i=0;i<10;i++){
      myStepper.step(100);
      delay(50);
 }
  myStepper.setSpeed(0);
  
//ultrasound Sensor
  while(1){                    // Wait 50ms between pings (about 20 pings/sec). 29ms should be the shortest delay between pings.
  unsigned int uS = sonar.ping(); // Send ping, get ping time in microseconds (uS).
  if((uS/US_ROUNDTRIP_CM)<5){
   
        myservo.write(180);      
         Serial.println(uS/US_ROUNDTRIP_CM);      
        Serial.println("Sonar pinged me");
        break;
    }
    Serial.println(uS/US_ROUNDTRIP_CM);
  }
  digitalWrite(52,HIGH);
  delay(3000);
    digitalWrite(52,LOW);
  }
  
 
}
