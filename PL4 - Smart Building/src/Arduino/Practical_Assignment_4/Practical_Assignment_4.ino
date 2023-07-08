// Pedro Martins (2019216826) & Mario Lemos (2019216792)
#include <Adafruit_MQTT.h>
#include <Adafruit_MQTT_Client.h>
#include <Adafruit_MQTT_FONA.h>

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <String.h>

// Introduce your SSID and PASSWORD from your Access Point as well as an Ip/Port for the MQTT broker and a name for your Arduino
#define ssid  "família pedro"
#define password  "martins123."
#define address "192.168.1.253"
#define port  1883
#define arduino_name "Arduino1"

#define T_COMMAND "address"

String tempToSend = "scm/pl4/rooms/" + String(arduino_name) + "/readings/temp";
String co2ToSend = "scm/pl4/rooms/" + String(arduino_name) + "/readings/co2";
String lightToSend = "scm/pl4/rooms/" + String(arduino_name) + "/readings/light";
String presenceToSend = "scm/pl4/rooms/" + String(arduino_name) + "/readings/presence";
String softwareUpdate = "scm/pl4/update/" + String(arduino_name);
String versionUpdate = "scm/pl4/rooms/" + String(arduino_name) + "/version";
String newDevice = "scm/pl4/newDevices/" + String(arduino_name);

String currentTemp = "" , currentCO2 = "", currentLight = "", currentPresence = "";
float version = 1.0;
int start = 0;

WiFiClient client;

Adafruit_MQTT_Client mqtt(&client, address, port);
Adafruit_MQTT_Publish temp = Adafruit_MQTT_Publish(&mqtt, tempToSend.c_str());
Adafruit_MQTT_Publish co2 = Adafruit_MQTT_Publish(&mqtt, co2ToSend.c_str());
Adafruit_MQTT_Publish light = Adafruit_MQTT_Publish(&mqtt, lightToSend.c_str());
Adafruit_MQTT_Publish presence = Adafruit_MQTT_Publish(&mqtt, presenceToSend.c_str());
Adafruit_MQTT_Publish device = Adafruit_MQTT_Publish(&mqtt, newDevice.c_str());
Adafruit_MQTT_Publish confirmUpdate = Adafruit_MQTT_Publish(&mqtt, versionUpdate.c_str());
Adafruit_MQTT_Subscribe update = Adafruit_MQTT_Subscribe(&mqtt, softwareUpdate.c_str());

extern "C"
{
  #include "user_interface.h"
}

void setup() {
  // Serial setup
  Serial.begin(115200);
  delay(10);

  // prepare LED
  pinMode(LED_BUILTIN, OUTPUT); 
  digitalWrite(LED_BUILTIN, 1);

  WiFiConnectionHandler();
  mqtt.subscribe(&update);
  connectMQTT();

  if (!device.publish("I'm a new device that has connected!"))
    Serial.println(F("\nCannot send data packet to the application!"));

  Serial.print("\nUse the keywords 'temp', 'c02', 'light' or 'presence' to change their values!");
}

void loop() {
  Serial.setTimeout(10000);
  String str;
  
  if (Serial.available() > 0){
    // Read new requests
    str = Serial.readStringUntil('\n');
    connectMQTT();
    // Check specification of new request
    if (str.equals("temp")){
      Serial.print("\nYou have 10 seconds to introduce a value for the temperature.");
      str = Serial.readStringUntil('\n');
      if (!currentTemp.equals(str.c_str())){
        if (!temp.publish(str.c_str()))
          Serial.println(F("\nCannot send data packet to the application!"));
      } else {
        Serial.println(F("\nYou need to input a different value than the current one!"));
      }
    } else if (str.equals("co2")){
      Serial.print("\nYou have 10 seconds to introduce a value for the CO2 levels.");
      str = Serial.readStringUntil('\n');
      if (!currentCO2.equals(str.c_str())){
        if (!co2.publish(str.c_str()))
          Serial.println(F("\nCannot send data packet to the application!"));
      } else {
        Serial.println(F("\nYou need to input a different value than the current one!"));
      }
    } else if (str.equals("light")){
      Serial.print("\nYou have 10 seconds to introduce a value for the room light.");
      str = Serial.readStringUntil('\n');
      if (!currentLight.equals(str.c_str())){
        if (!light.publish(str.c_str()))
          Serial.println(F("\nCannot send data packet to the application!"));
      } else {
        Serial.println(F("\nYou need to input a different value than the current one!"));
      }
    } else if (str.equals("presence")){
      Serial.print("\nYou have 10 seconds to introduce a value for the room presence.");
      str = Serial.readStringUntil('\n');
      if (!currentPresence.equals(str.c_str())){
        if (!presence.publish(str.c_str()))
          Serial.println(F("\nCannot send data packet to the application!"));
      } else {
        Serial.println(F("\nYou need to input a different value than the current one!"));
      }
    } else{
      Serial.print("\nUnrecognized input, please try again!");
    }
  }
  if (start == 1)
    checkUpdate();
  start = 1;
  mqtt.disconnect();
}

// Function for Access Point connection to the credentials given at the beginning of the code
void WiFiConnectionHandler(){
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

// Function to handle the connection to the MQTT Broker
void connectMQTT() {
  int8_t ret;

  // Check if a MQTT connection is already established
  if (mqtt.connected()) {
    return;
  }

  //Serial.print("\nConnecting to MQTT... ");

  // Try to connect to the given MQTT Ip/Port, in case of failure the board will continue the connection attempt. 
  while ((ret = mqtt.connect()) != 0) { // connect will return 0 for connected
    Serial.println(mqtt.connectErrorString(ret));
    Serial.println("Retrying MQTT connection in 5 seconds...");
    mqtt.disconnect();
    delay(5000);  // wait 5 seconds
  }
  //Serial.println("MQTT Connected!\n");
}

// Function to check for software updates provided by the management application.
void checkUpdate(){
  char versionSend[8], compare[8];

  Adafruit_MQTT_Subscribe *subscription;
  while ((subscription = mqtt.readSubscription(5000))) {
    if (subscription == &update) {
      dtostrf(version, 4, 2, compare);
      if (strcmp((char *)update.lastread, compare) != 0){
        //Serial.print(F("\nGot: "));
        //Serial.println((char *)update.lastread);
        //Serial.println(version);
        Serial.print("\nNew update found! Updating the software to the latest version ");
        Serial.println((char *)update.lastread);
        version = version + 0.1;
        for (int i = 0; i < 2; i++){
          digitalWrite(LED_BUILTIN, 0);
          delay(500);
          digitalWrite(LED_BUILTIN, 1);
          delay(500);
        }
        dtostrf(version, 4, 2, versionSend);
        Serial.print("\nSoftware successfully updated!");
        //Serial.println(versionSend);
        if (!confirmUpdate.publish(versionSend))
            Serial.println(F("\nCannot send data packet to the application!"));
      }     
    }
  }
}