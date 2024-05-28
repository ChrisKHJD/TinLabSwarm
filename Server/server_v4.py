import socket
import threading
import json
import math
import time
from datetime import datetime
from time import sleep

HOST = "145.24.223.115"
PORT = 8000
# HOST = "145.137.54.196"
# PORT = 8000

connectedClients = {}  #id, client_socket, client_address
webots = {}  #id, location, last message time
chariots = {}  #id, location, direction, last message time

#format used for instructions calculation
# webots = {
#     0: (15, 20),  # Target position for robot_0
#     1: (25, 30),  # Target position for robot_1
#     2: (5, 15),   # Target position for robot_2
# }
#
# chariots = {
#     0: (10, 10, 30),  # Real position and orientation for robot_0
#     1: (20, 25, 60),  # Real position and orientation for robot_1
#     2: (2, 10, 90),   # Real position and orientation for robot_2
# }


# Calculate the angle between two points.
def calculate_angle(x1, y1, x2, y2):
    return math.degrees(math.atan2(y2 - y1, x2 - x1))


# Calculate the smallest difference between two angles.
def angle_difference(angle1, angle2):
    return (angle1 - angle2 + 180) % 360 - 180


# Calculate the Euclidean distance between two points.
def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


# Generate movement instructions for robot to reach target. test threshold value
def get_instruction(robot_id, target_x, target_y, real_x, real_y, orientation, threshold=0.5):
    instruction = ""

    target_angle = calculate_angle(real_x, real_y, target_x, target_y)
    angle_diff = angle_difference(target_angle, orientation)

    if distance(real_x, real_y, target_x, target_y) <= threshold:
        instruction = 'stop'
    elif abs(angle_diff) < 5:  # Within 5 degrees, move forward (maybe lower this value)
        instruction = 'move_forward'
    elif angle_diff > 0:
        instruction = 'rotate_right'
    else:
        instruction = 'rotate_left'

    return instruction


def chariot_instructions():
    global chariots

    while True:
        for chariot in chariots:
            print(chariot, chariots[chariot])

            client_socket = connectedClients[chariot]["client_socket"]

            # add camera and pathplanning code here
            # real_x, real_y, orientation = chariots[chariot]
            # target_x, target_y = webots[chariot]
            # instr = get_instruction(chariot, target_x, target_y, real_x, real_y, orientation)
            # print(time.time(), 'instruction send:', chariot, instr)

            payload_send = {
                # "instruction": "turn_left"  #instr
                # "instruction": "turn_right"
                # "instruction": "move"
                "instruction": "back_led_on"
            }

            try:
                # stuur je alle instructies naar alle robots? de robot zelf weet niet welk id die heeft?
                client_socket.sendall(json.dumps(payload_send).encode("ascii"))
                print("\tdata sent")
            except:
                print("\tnothing sent, connection lost")
                break

        sleep(5)


def camera():
    while True:
        print("hello")
        sleep(50)


def receiving(client_socket, client_address, client_id):
    global webots, chariots

    while True:
        print(f"{client_id}, trying to receive")

        try:
            payload_received = json.loads(client_socket.recv(1024).decode())
            print(payload_received)

            if payload_received["type"] == "chariot":
                chariots[client_id] = payload_received
                print("success")
                return
            
            webots = payload_received
        except:
            print(f"{client_id}, no data received")

        sleep(0.1)


def main():
    global connectedClients

    clientCount = 0

    t = threading.Thread(
        target=chariot_instructions,
        args=(),
    )
    t.start()

    t = threading.Thread(
        target=camera,
        args=(),
    )
    t.start()

    print(f"start server on: {HOST} {PORT}")
    s = socket.create_server((HOST, PORT))
    s.listen()

    while True:
        client_socket, client_address = s.accept()
        clientCount += 1
        print("connection accepted from ", client_address)

        connectedClients[clientCount] = {
            "client_socket": client_socket,
            "client_address": client_address
        }

        t = threading.Thread(
            target=receiving,
            args=(
                client_socket,
                client_address,
                clientCount
            ),
        )
        t.start()

        print(clientCount, " clients connected")


main()
