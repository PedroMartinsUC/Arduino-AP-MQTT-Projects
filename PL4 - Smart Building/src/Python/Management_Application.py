# Pedro Martins (2019216826) & Mario Lemos (2019216792)

from paho.mqtt import client as mqtt_client
from threading import Thread
import threading
import random
import time
import sys
from datetime import datetime

# Configure according to the broker's IP and PORT
broker = '192.168.1.253'
port = 1883
topic_receive_data = "scm/pl4/rooms/#"
topic_shutdown_hvac = "scm/pl4/hvac_status"
topic_shutdown_lights = "scm/pl4/light-controller_status"
topic_receive_devices = "scm/pl4/newDevices/#"
client_id = f'python-mqtt-{random.randint(0, 100)}'

newDeviceFlag = False

thresholds = {

}

# "room1": ["temp", "co2", "light", "presence", "version", "heater", "cooler", "ventilator", "lights"]
current_info = {

}

thread_counter = 1


def light_manager(topic):
    if int(current_info[topic.split("/")[3]][3]) == 0:
        if current_info[topic.split("/")[3]][8] == "ON":
            current_info[topic.split("/")[3]][8] = "OFF"
            send_info("scm/pl4/rooms/" + topic.split("/")[3] + "/lights", "OFF", client, 0)
    else:
        if int(thresholds[topic.split("/")[3]][6]) > int(current_info[topic.split("/")[3]][2]):
            if current_info[topic.split("/")[3]][8] == "OFF":
                current_info[topic.split("/")[3]][8] = "ON"
                send_info("scm/pl4/rooms/" + topic.split("/")[3] + "/lights", "ON", client, 0)
        else:
            if current_info[topic.split("/")[3]][8] == "ON":
                current_info[topic.split("/")[3]][8] = "OFF"
                send_info("scm/pl4/rooms/" + topic.split("/")[3] + "/lights", "OFF", client, 0)


def turn_off(index):
    if index == 0:
        for key in current_info.keys():
            current_info[key][8] = "OFF"
        print_info(" > Lights shutdown")
    else:
        for key in current_info.keys():
            current_info[key][5] = "OFF"
            current_info[key][6] = "OFF"
            current_info[key][7] = "OFF"
        print_info(" > Heater, cooler and ventilation shutdown")


def information(name):
    if name in current_info.keys():
        print_info("-----------------" + name + " Information Details-----------------")
        string = "| The lights are turned: " + current_info[name][8] + \
                 "\n| The room temperature is: " + current_info[name][0] + \
                 "\n| The cooler is turned: " + current_info[name][6] + \
                 "\n| The heater is turned: " + current_info[name][5] + \
                 "\n| The ventilation is turned: " + current_info[name][7] + \
                 "\n| The number of people in the room is: " + current_info[name][3] + \
                 "\n| The level of co2 is: " + current_info[name][1] + \
                 "\n| The level of light is: " + current_info[name][2] + \
                 "\n| The current software version is: " + current_info[name][4]
        print(string)
        print_info("--------------------------------------------------------------")
    else:
        print_info(" > The device doesnt exist")


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print_info(" > Connected to MQTT Broker!")
        else:
            print(datetime.now().strftime("%H:%M:%S") + " > Failed to connect, return code %d", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def send_info(topic, info, client, update):
    if update == 1:
        for i in range(info):
            topicSend = "scm/pl4/update/" + topic.split("/")[i]
            current_info[topic.split("/")[i]][4] = str(
                format(round(float(current_info[topic.split("/")[i]][4]) + 0.1, 2), '.2f'))
            result = client.publish(topicSend, current_info[topic.split("/")[i]][4], retain=True)
            status = result[0]
            if status != 0:
                print_info(f" > Failed to send message to topic {topicSend}")
    else:
        result = client.publish(topic, info, retain=True)
        status = result[0]
        if status != 0:
            print_info(f" > Failed to send message to topic {topic}")


def update_info(topic, info):
    if topic.split("/")[5] == "temp":
        current_info[topic.split("/")[3]][0] = info
    elif topic.split("/")[5] == "co2":
        current_info[topic.split("/")[3]][1] = info
    elif topic.split("/")[5] == "light":
        current_info[topic.split("/")[3]][2] = info
        light_manager(topic)
    elif topic.split("/")[5] == "presence":
        current_info[topic.split("/")[3]][3] = info
        light_manager(topic)


def update_sensors(topic, info, identifier):
    current_info[topic.split("/")[3]][identifier] = info


def subscribe(client: mqtt_client, e):
    def on_message(client, userdata, msg):
        global newDeviceFlag
        if msg.topic.split("/")[2] == "newDevices":
            current_info[msg.topic.split("/")[3]] = ["Undefined", "Undefined", "0", "0", "1.0", "OFF", "OFF", "OFF", "OFF"]
            thresholds[msg.topic.split("/")[3]] = ["0"] * 7
            client.publish("scm/pl4/update/" + msg.topic.split("/")[3], "1.00", retain=True)
            newDeviceFlag = True
            e.clear()
            welcome(msg.topic.split("/")[3])
            newDeviceFlag = False
            e.set()
            send_info("scm/pl4/rooms/" + msg.topic.split("/")[3] + "/thresholds",
                      thresholds[msg.topic.split("/")[3]][0] + "/" + thresholds[msg.topic.split("/")[3]][1] + "/" +
                      thresholds[msg.topic.split("/")[3]][
                          2] + "/" + thresholds[msg.topic.split("/")[3]][3] + "/" + thresholds[msg.topic.split("/")[3]][
                          4] + "/" + thresholds[msg.topic.split("/")[3]][
                          5], client, 0)
        elif msg.topic.split("/")[2] == "light-controller_status":
            turn_off(0)
        elif msg.topic.split("/")[2] == "hvac_status":
            turn_off(1)
        elif msg.topic.split("/")[4] == "readings":
            update_info(msg.topic, msg.payload.decode())
        elif msg.topic.split("/")[4] == "version":
            if current_info[msg.topic.split("/")[3]][4] == msg.payload.decode():
                print_info(" > Device successfully updated!")
        elif msg.topic.split("/")[4] == "cooler":
            update_sensors(msg.topic, msg.payload.decode(), 6)
        elif msg.topic.split("/")[4] == "heater":
            update_sensors(msg.topic, msg.payload.decode(), 5)
        elif msg.topic.split("/")[4] == "ventilation":
            update_sensors(msg.topic, msg.payload.decode(), 7)

    client.subscribe(topic_receive_data)
    client.subscribe(topic_receive_devices)
    client.subscribe(topic_shutdown_hvac)
    client.subscribe(topic_shutdown_lights)
    client.on_message = on_message


def run(arg, e):
    global client
    if arg == 1:
        e.set()
        client = connect_mqtt()

        print_info(" > Welcome to the Management Application!")

        subscribe(client, e)
        client.loop_forever()

    else:
        time.sleep(1)
        print_info(" > Type 'help' for a list of commands!")
        while True:
            event_set = e.wait()
            start = input(datetime.now().strftime("%H:%M:%S") + " > Introduce the command: \n")
            if start == "update":
                device_list = list(current_info)
                if len(current_info) == 0:
                    print_info(" > No devices registered!")
                else:
                    count = 0
                    toSend = ""
                    for i in range(len(current_info)):
                        print_info(" > [" + str(i + 1) + "] " + device_list[i] + " running on version " +
                              current_info[device_list[i]][4])
                    print_info(" > Use the numbers above to guide the devices to a new software update and type STOP to send the message!")
                    while True:
                        start = input(datetime.now().strftime("%H:%M:%S") + " > Introduce the number of the device: ")
                        if start == "STOP":
                            break
                        toSend += device_list[int(start) - 1] + "/"
                        count += 1
                    send_info(toSend, count, client, 1)
            elif start == "info":
                name = input(datetime.now().strftime("%H:%M:%S") + " > Input the name of the device: ")
                information(name)
            elif start == "thresholds":
                name = input(datetime.now().strftime("%H:%M:%S") + " > Input the name of the device: ")
                new_thresholds(name)
            elif start == "help":
                print_info(" > Commands: ")
                print("update     -> Update the software")
                print("info       -> Get detailed information about a selected device")
                print("thresholds -> Update the thresholds of a selected device")
                print("help       -> List of valid commands")
                print("--------------------------------------------------------------")
            else:
                print_info(" > Command not found!")


def welcome(room):
    print_info(" > ----------New Device Detected----------")
    print_info(" > A new device has connected! Please set its boundaries: ")
    thresholds[room][0] = input("Minimum of room temperature with human presence: ")
    thresholds[room][1] = input("Maximum of room temperature with human presence: ")
    thresholds[room][2] = input("Minimum of room temperature without human presence: ")
    thresholds[room][3] = input("Maximum of room temperature without human presence: ")
    thresholds[room][4] = input("Safe level of CO2: ")
    thresholds[room][5] = input("Max level of CO2: ")
    thresholds[room][6] = input("Crepuscular sensor threshold: ")
    print_info("----------------------------------------------------")


def new_thresholds(room):
    if room in thresholds.keys():
        print_info(" > Please set new thresholds: ")
        thresholds[room][0] = input("Minimum of room temperature with human presence: ")
        thresholds[room][1] = input("Maximum of room temperature with human presence: ")
        thresholds[room][2] = input("Minimum of room temperature without human presence: ")
        thresholds[room][3] = input("Maximum of room temperature without human presence: ")
        thresholds[room][4] = input("Safe level of CO2: ")
        thresholds[room][5] = input("Max level of CO2: ")
        thresholds[room][6] = input("Crepuscular sensor threshold: ")
        light_manager("scm/pl4/rooms/" + room)
        print("----------------------------------------------------")
        send_info("scm/pl4/rooms/" + room + "/thresholds",
                  thresholds[room][0] + "/" + thresholds[room][1] + "/" +
                  thresholds[room][
                      2] + "/" + thresholds[room][3] + "/" +
                  thresholds[room][
                      4] + "/" + thresholds[room][
                      5], client, 0)
    else:
        print_info(" > The device doesnt exist!")


def print_info(message):
    print(datetime.now().strftime("%H:%M:%S") + message)


if __name__ == '__main__':
    try:
        e = threading.Event()
        read = Thread(target=run, args=(2, e,))
        read.start()
        thread_counter += 1
        run(1, e)
    except KeyboardInterrupt:
        print_info(" > Received termination signal, sending will...")
        sys.exit(-1)
    except Exception as e:
        print_info(" > Exception encountered: " + str(e))
        print_info(" > Received termination signal, sending will...")
        sys.exit(-2)