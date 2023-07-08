# Pedro Martins (2019216826) & Mario Lemos (2019216792)

from paho.mqtt import client as mqtt_client
from threading import Thread
import random
import time
import re

# Configure according to the broker's IP and PORT
broker = '192.168.1.254'
port = 1883
topic_receive = "scm/pl3/sniffer/#"
topic_receive_new_devices = "scm/pl3/newDevices"
topic_send = "scm/pl3/addresses"
client_id = f'python-mqtt-{random.randint(0, 100)}'

thread_counter = 1
thread_flag = False


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!\n")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def threaded_function(arg):
    for i in range(arg):
        print("running")
        time.sleep(1)


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        global thread_counter
        print(msg.payload.decode())
        print("-> This packet was found at: " + msg.topic)
        print()
        if msg.topic == topic_receive_new_devices and thread_flag:
            thread_counter+= 1
            print("aqui")
            thread = Thread(run())
            thread.start()
        # print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    client.subscribe(topic_receive)
    client.subscribe(topic_receive_new_devices)
    client.on_message = on_message


def publish(client):
    msg_count = 0
    while True:
        time.sleep(1)
        msg = f"messages: {msg_count}"
        result = client.publish(topic_send, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic_send}`")
        else:
            print(f"Failed to send message to topic {topic_send}")
        msg_count += 1


def run():
    global thread_flag
    addresses = ""
    client = connect_mqtt()

    macNum = input("Welcome to the management application! Please introduce the number of MAC Addresses to search: ")
    for i in range(int(macNum)):
        correct = 0
        while correct == 0:
            temp = input("Introduce the MAC Address " + str(i) + ": ")
            if re.findall("^[a-z0-9]{2}\:[a-z0-9]{2}\:[a-z0-9]{2}\:[a-z0-9]{2}\:[a-z0-9]{2}\:[a-z0-9]{2}$", temp):
                correct = 1
            else:
                print("The MAC Address must follow the format xx:xx:xx:xx:xx:xx")
        addresses += temp + " "

    print(addresses)
    thread_flag = True
    result = client.publish(topic_send, addresses)
    status = result[0]
    if status == 0:
        print(f"Send `{addresses}` to topic `{topic_send}`")
    else:
        print(f"Failed to send message to topic {topic_send}")

    subscribe(client)
    client.loop_forever()


if __name__ == '__main__':
    run()
    while thread_counter!=1:
        thread_counter-= 1
        thread.join()

