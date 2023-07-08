// Pedro Martins (2019216826) & Mario Lemos (2019216792)
#include <Adafruit_MQTT.h>
#include <Adafruit_MQTT_Client.h>
#include <Adafruit_MQTT_FONA.h>

#include <Arduino.h>
#include <ESP8266WiFi.h>
#include "sdk_structs.h"
#include "ieee80211_structs.h"
#include "string_utils.h"
#include <String.h>

// Introduce your SSID and PASSWORD from your Access Point as well as an Ip/Port for the MQTT broker and a name for your Arduino
#define ssid  "família pedro"
#define password  "martins123."
#define address "192.168.1.253"
#define port  1883
#define arduino_name "Arduino1"

#define T_COMMAND "address"

// Global Variables for data interpertation and flags
int channel_change = 1;
int flag = 0;
int received = 0;
int count = 0;
String matching[20];
String toSend;
String addressToSend = "scm/pl3/sniffer/" + String(arduino_name); 

WiFiClient client;

Adafruit_MQTT_Client mqtt(&client, address, port);
Adafruit_MQTT_Publish data = Adafruit_MQTT_Publish(&mqtt, addressToSend.c_str());
Adafruit_MQTT_Publish dataNew = Adafruit_MQTT_Publish(&mqtt, "scm/pl3/newDevices");
Adafruit_MQTT_Subscribe addresses = Adafruit_MQTT_Subscribe(&mqtt, "scm/pl3/addresses");

extern "C"
{
  #include "user_interface.h"
}

// According to the SDK documentation, the packet type can be inferred from the
// size of the buffer. We are ignoring this information and parsing the type-subtype
// from the packet header itself. Still, this is here for reference.
wifi_promiscuous_pkt_type_t packet_type_parser(uint16_t len)
{
    switch(len)
    {
      // If only rx_ctrl is returned, this is an unsupported packet
      case sizeof(wifi_pkt_rx_ctrl_t):
      return WIFI_PKT_MISC;

      // Management packet
      case sizeof(wifi_pkt_mgmt_t):
      return WIFI_PKT_MGMT;

      // Data packet
      default:
      return WIFI_PKT_DATA;
    }
}

// Packet sniffed from network handling.
void wifi_sniffer_packet_handler(uint8_t *buff, uint16_t len)
{
  // First layer: type cast the received buffer into our generic SDK structure
  const wifi_promiscuous_pkt_t *ppkt = (wifi_promiscuous_pkt_t *)buff;
  // Second layer: define pointer to where the actual 802.11 packet is within the structure
  const wifi_ieee80211_packet_t *ipkt = (wifi_ieee80211_packet_t *)ppkt->payload;
  // Third layer: define pointers to the 802.11 packet header and payload
  const wifi_ieee80211_mac_hdr_t *hdr = &ipkt->hdr;
  const uint8_t *data = ipkt->payload;

  // Pointer to the frame control section within the packet header
  const wifi_header_frame_control_t *frame_ctrl = (wifi_header_frame_control_t *)&hdr->frame_ctrl;

  // Parse MAC addresses contained in packet header into human-readable strings
  char addr1[] = "00:00:00:00:00:00\0";
  char addr2[] = "00:00:00:00:00:00\0";
  char addr3[] = "00:00:00:00:00:00";

  mac2str(hdr->addr1, addr1);
  mac2str(hdr->addr2, addr2);
  mac2str(hdr->addr3, addr3);

  // Loop for all the MAC Addresses given by the application
  for (int i = 0; i < count; i++){
    if (strcmp(addr3, matching[i].c_str()) == 0){
      toSend = "***** Pacote Encontrado *****\n-> Endereco MAC: " + String(addr3) + "\n-> Channel Encontrado: " + wifi_get_channel() + "\n-> RSSI: " + ppkt->rx_ctrl.rssi;
      flag = 1;
    }
  }
}
// c8:b4:22:b3:42:97

// Arduino setup function
void setup()
{
  // Serial setup
  Serial.begin(115200);
  delay(10);
  wifi_set_channel(1);

  // prepare LED
  pinMode(LED_BUILTIN, OUTPUT); 
  digitalWrite(LED_BUILTIN, 1);

  // prepare WiFi, MQTT and Promiscuous mode operations
  WiFiConnectionHandler(); 
  mqtt.subscribe(&addresses);
  connectMQTT();
  if (!dataNew.publish("I'm a new device that has connected!")){
    Serial.println(F("\nCannot send data packet to the application!"));
  } else {
    Serial.println(F("\nData packet has been sent to the application successfully!"));
  }
  receiveAddresses();
  
  
  wifi_set_opmode(STATION_MODE);
  wifi_promiscuous_enable(0);
  WiFi.disconnect();

  wifi_set_promiscuous_rx_cb(wifi_sniffer_packet_handler);
  wifi_promiscuous_enable(1);

}

// Arduino loop function
void loop(){
  // Change channel to detect other packets 
  channel_change = (channel_change + 1) % 13;
  wifi_set_channel(channel_change);
  delay(10);

  // If addresses are received, start the promiscuous search
  if(received == 1){
    // If desired packet is found, re-enable WiFi and MQTT capabilities and publish information to application
    if (flag == 1){
      wifi_promiscuous_enable(0);
      WiFiConnectionHandler(); 
      connectMQTT();

      digitalWrite(LED_BUILTIN, 0);
      Serial.println(toSend);

      if (!data.publish(toSend.c_str())){
        Serial.println(F("\nCannot send data packet to the application!"));
      } else {
        Serial.println(F("\nData packet has been sent to the application successfully!"));
      }

      delay(2000);
      digitalWrite(LED_BUILTIN, 1);
    
      flag = 0;
      wifi_promiscuous_enable(1);
    }
  }
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

  Serial.print("\nConnecting to MQTT... ");

  // Try to connect to the given MQTT Ip/Port, in case of failure the board will continue the connection attempt. 
  while ((ret = mqtt.connect()) != 0) { // connect will return 0 for connected
    Serial.println(mqtt.connectErrorString(ret));
    Serial.println("Retrying MQTT connection in 5 seconds...");
    mqtt.disconnect();
    delay(5000);  // wait 5 seconds
  }
  Serial.println("MQTT Connected!\n");
}

// Function to work within the setup phase, necessary to receive the addresses to sniff from the control application
void receiveAddresses(){
  String str;

  // Continue to try until successful reading of addresses  
  while (received == 0){
    Adafruit_MQTT_Subscribe *subscription;
    while ((subscription = mqtt.readSubscription(5000))) {
      if (subscription == &addresses) {
        received = 1;
               
        str = (char *)addresses.lastread;
        while (str.length() > 0){
          int index = str.indexOf(' ');
          if (index == -1){
            matching[count++] = str;
            break;
          }
          else{
            matching[count++] = str.substring(0, index);
            str = str.substring(index+1);
          }
        }
        
        // Print the addresses obtained from the application
        Serial.print("List of Addresses to search: \n");
        for (int i = 0; i < count; i++){
          Serial.print("-> ");
          Serial.print(i);
          Serial.print(": \"");
          Serial.print(matching[i]);
          Serial.println("\"");
        }  
      }
    }
  }
}