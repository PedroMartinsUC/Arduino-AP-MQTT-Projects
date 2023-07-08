# Pedro Martins (2019216826) & Mario Lemos (2019216792)

from paho.mqtt import client as mqtt_client
import random
from datetime import datetime
import sys

# Configure according to the broker's IP and PORT
broker = '192.168.1.253'
port = 1883
topic_receive_data = "scm/pl4/rooms/#"
client_id = f'python-mqtt-{random.randint(0, 100)}'


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print_info(" > Connected to MQTT Broker!")
        else:
            print(datetime.now().strftime("%H:%M:%S") + " > Failed to connect, return code %d")

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.will_set("scm/pl4/light-controller-status", "SHUTDOWN", 0, False)
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        if msg.topic.split("/")[4] == "lights":
            print_info(" > Turning the lights " + msg.payload.decode() + " in room " + msg.topic.split("/")[3])

    client.subscribe(topic_receive_data)
    client.on_message = on_message


def print_info(message):
    print(datetime.now().strftime("%H:%M:%S") + message)


def run():
    client = connect_mqtt()
    print_info(" > Booting up Lights Manager...")
    print_info(" > Welcome to the Lights Control Unit!")
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print_info(" > Received termination signal, sending will...")
        print_info(" > Will sent! Lights Unit shutting down!")
        sys.exit(-1)
    except Exception as e:
        print_info(" > Exception encountered: " + str(e))
        print_info(" > Received termination signal, sending will...")
        print_info(" > Will sent! Lights Unit shutting down!")
        sys.exit(-2)