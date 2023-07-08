# Pedro Martins (2019216826) & Mario Lemos (2019216792)

from datetime import datetime
from paho.mqtt import client as mqtt_client
import random
import sys

# Configure according to the broker's IP and PORT
broker = '192.168.1.253'
port = 1883
topic_receive_thresholds = "scm/pl4/rooms/+/thresholds"
topic_receive_sensordata = "scm/pl4/rooms/+/readings/#"
client_id = f'python-mqtt-{random.randint(0, 100)}'

# [Limits, Heater, Cooler, Ventilation]
thresholds = {

}

# [Temperature, CO2, Presence]
current_info = {

}


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print_info(" > Connected to MQTT Broker!")
        else:
            print(datetime.now().strftime("%H:%M:%S") + " > Failed to connect, return code %d", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.will_set("scm/pl4/hvac_status", "SHUTDOWN", 0, False)
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        if msg.topic.split("/")[4] == "thresholds":
            if msg.topic.split("/")[3] in thresholds.keys():
                print_info(" > New thresholds: " + msg.topic.split("/")[3] + " has received new limits: \n           - "
                                                                             "Minimum Temperature With Presence: " + msg.payload.decode().split("/")[0] + "\n           - "
                                                                             "Maximum Temperature With Presence: " + msg.payload.decode().split("/")[1] + "\n           - "
                                                                             "Minimum Temperature Without Presence: " + msg.payload.decode().split("/")[2] + "\n           - "
                                                                             "Maximum Temperature Without Presence: " + msg.payload.decode().split("/")[3] + "\n           - "
                                                                             "Safe Levels of CO2: " + msg.payload.decode().split("/")[4] + "\n           - "
                                                                             "Hazardous Levels of CO2: " + msg.payload.decode().split("/")[5])
                thresholds[msg.topic.split("/")[3]][0] = msg.payload.decode()
                if current_info[msg.topic.split("/")[3]][0] != "Undefined":
                    checkTemp(current_info[msg.topic.split("/")[3]][0], msg.topic.split("/")[3], client)
                if current_info[msg.topic.split("/")[3]][1] != "Undefined":
                    checkCO2(current_info[msg.topic.split("/")[3]][1], msg.topic.split("/")[3], client)
            else:
                print_info(" > New thresholds: " + msg.topic.split("/")[3] + " has set their limits as: \n           - "
                                                                             "Minimum Temperature With Presence: " + msg.payload.decode().split("/")[0] + "\n           - "
                                                                             "Maximum Temperature With Presence: " + msg.payload.decode().split("/")[1] + "\n           - "
                                                                             "Minimum Temperature Without Presence: " + msg.payload.decode().split("/")[2] + "\n           - "  
                                                                             "Maximum Temperature Without Presence: " + msg.payload.decode().split("/")[3] + "\n           - "
                                                                             "Safe Levels of CO2: " + msg.payload.decode().split("/")[4] + "\n           - "
                                                                             "Hazardous Levels of CO2: " + msg.payload.decode().split("/")[5])
                thresholds[msg.topic.split("/")[3]] = [msg.payload.decode(), "OFF", "OFF", "OFF"]
                current_info[msg.topic.split("/")[3]] = ["Undefined", "Undefined", "Undefined"]
        else:
            if msg.topic.split("/")[5] == "temp":
                current_info[msg.topic.split("/")[3]][0] = msg.payload.decode()
                checkTemp(msg.payload.decode(), msg.topic.split("/")[3], client)
            elif msg.topic.split("/")[5] == "co2":
                current_info[msg.topic.split("/")[3]][1] = msg.payload.decode()
                checkCO2(msg.payload.decode(), msg.topic.split("/")[3], client)
            elif msg.topic.split("/")[5] == "presence":
                current_info[msg.topic.split("/")[3]][2] = msg.payload.decode()
                checkTemp(msg.payload.decode(), msg.topic.split("/")[3], client)

    client.subscribe(topic_receive_thresholds)
    client.subscribe(topic_receive_sensordata)
    client.on_message = on_message


def checkTemp(value, room, client):
    if current_info[room][2] == "Undefined" or int(current_info[room][2]) == 0:
        if int(value) < int(thresholds[room][0].split("/")[2]):
            if thresholds[room][1] == "OFF":
                if thresholds[room][2] == "ON":
                    print_info(" > Change of status: " + room + " Cooler is now OFF")
                    thresholds[room][2] = "OFF"
                    client.publish("scm/pl4/rooms/" + room + "/cooler", "OFF")
                print_info(" > Change of status: " + room + " Heater is now ON")
                thresholds[room][1] = "ON"
                client.publish("scm/pl4/rooms/" + room + "/heater", "ON")
                return
        elif int(value) > int(thresholds[room][0].split("/")[3]):
            if thresholds[room][2] == "OFF":
                if thresholds[room][1] == "ON":
                    print_info(" > Change of status: " + room + " Heater is now OFF")
                    thresholds[room][1] = "OFF"
                    client.publish("scm/pl4/rooms/" + room + "/heater", "OFF")
                print_info(" > Change of status: " + room + " Cooler is now ON")
                thresholds[room][2] = "ON"
                client.publish("scm/pl4/rooms/" + room + "/cooler", "ON")
                return
    else:
        if int(value) < int(thresholds[room][0].split("/")[0]):
            if thresholds[room][1] == "OFF":
                if thresholds[room][2] == "ON":
                    print_info(" > Change of status: " + room + " Cooler is now OFF")
                    thresholds[room][2] = "OFF"
                    client.publish("scm/pl4/rooms/" + room + "/cooler", "OFF")
                print_info(" > Change of status: " + room + " Heater is now ON")
                thresholds[room][1] = "ON"
                client.publish("scm/pl4/rooms/" + room + "/heater", "ON")
                return
        elif int(value) > int(thresholds[room][0].split("/")[1]):
            if thresholds[room][2] == "OFF":
                if thresholds[room][1] == "ON":
                    print_info(" > Change of status: " + room + " Heater is now OFF")
                    thresholds[room][1] = "OFF"
                    client.publish("scm/pl4/rooms/" + room + "/heater", "OFF")
                print_info(" > Change of status: " + room + " Cooler is now ON")
                thresholds[room][2] = "ON"
                client.publish("scm/pl4/rooms/" + room + "/cooler", "ON")
                return

    if thresholds[room][1] == "ON":
        print_info(" > Change of status: " + room + " Heater is now OFF")
        thresholds[room][1] = "OFF"
        client.publish("scm/pl4/rooms/" + room + "/heater", "OFF")
    elif thresholds[room][2] == "ON":
        print_info(" > Change of status: " + room + " Cooler is now OFF")
        thresholds[room][2] = "OFF"
        client.publish("scm/pl4/rooms/" + room + "/cooler", "OFF")


def checkCO2(value, room, client):
    if int(value) > int(thresholds[room][0].split("/")[5]):
        if thresholds[room][3] == "OFF":
            print_info(" > Change of status: " + room + " Ventilation is now ON")
            thresholds[room][3] = "ON"
            client.publish("scm/pl4/rooms/" + room + "/ventilation", "ON")
    elif int(value) < int(thresholds[room][0].split("/")[4]):
        if thresholds[room][3] == "ON":
            print_info(" > Change of status: " + room + " Ventilation is now OFF")
            thresholds[room][3] = "OFF"
            client.publish("scm/pl4/rooms/" + room + "/ventilation", "OFF")


def print_info(message):
    print(datetime.now().strftime("%H:%M:%S") + message)


def run():
    client = connect_mqtt()
    print_info(" > Booting up HVAC Unity...")
    print_info(" > Welcome to the HVAC Control Unit!")
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print_info(" > Received termination signal, sending will...")
        print_info(" > Will sent! HVAC Unit shutting down!")
        sys.exit(-1)
    except Exception as e:
        print_info(" > Exception encountered: " + str(e))
        print_info(" > Received termination signal, sending will...")
        print_info(" > Will sent! HVAC Unit shutting down!")
        sys.exit(-2)
