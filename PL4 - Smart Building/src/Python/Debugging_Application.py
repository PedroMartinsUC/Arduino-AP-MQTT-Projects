# Pedro Martins (2019216826) & Mario Lemos (2019216792)

from datetime import datetime
from paho.mqtt import client as mqtt_client
import random
import sys

# Configure according to the broker's IP and PORT
broker = '192.168.1.253'
port = 1883
topic_receive = "scm/pl4/#"
client_id = f'python-mqtt-{random.randint(0, 100)}'


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print_info(" > Connected to MQTT Broker!")
        else:
            print(datetime.now().strftime("%H:%M:%S") + " > Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print_info(f" > Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(topic_receive)
    client.on_message = on_message


def print_info(message):
    print(datetime.now().strftime("%H:%M:%S") + message)


def run():
    client = connect_mqtt()
    print_info(" > Booting up Debugging Application...")
    print_info(" > Welcome to the Debugging Application!")
    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    try:
        run()
    except KeyboardInterrupt:
        print_info(" > Received termination signal, shutting down...")
        sys.exit(-1)
    except Exception as e:
        print_info(" > Exception encountered: " + str(e))
        print_info(" > Received termination signal, shutting down...")
        sys.exit(-2)