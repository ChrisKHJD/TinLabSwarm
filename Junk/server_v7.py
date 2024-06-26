import socket
import threading
import json
import math
import time
from datetime import datetime
from time import sleep
from random import randint
from colorama import Fore, Style

from newRobotTracking import process_frame_and_return_chariots

# HOST = "145.24.223.115"
# PORT = 8000
HOST = "145.24.243.10"
PORT = 8000

clientCount = 0

connectedClients = {}  #id, client_socket, client_address
webots = {}  #id, location, last message time
chariots = {} #id, location, direction, last message time

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
def angle_to_target(front_x, front_y, target_x, target_y, orientation):
    target_angle = math.degrees(math.atan2(target_y - front_y, target_x - front_x))
    angle_diff = target_angle - orientation
    return (angle_diff + 180) % 360 - 180  # normalize to [-180, 180]


# Calculate the smallest difference between two angles.
def angle_difference(angle1, angle2):
    difference = (angle1 - angle2 + 180) % 360 - 180
    if difference < -180:
        difference += 360
    elif difference > 180:
        difference -= 360
    return difference


# Calculate the Euclidean distance between two points.
def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


# Generate movement instructions for robot to reach target. test threshold value
def get_instruction(robot_id, target_x, target_y, real_x, real_y, orientation, threshold=20):
    instruction = ""
    angle_diff = angle_to_target(real_x, real_y, target_x, target_y, orientation)
    print(f"{robot_id}: \t {Fore.CYAN}angle_diff: {angle_diff}{Style.RESET_ALL}, {Fore.WHITE}orientation: {orientation}{Style.RESET_ALL}, {Fore.MAGENTA}distance: {distance(real_x, real_y, target_x, target_y)}{Style.RESET_ALL}")

    if distance(real_x, real_y, target_x, target_y) <= threshold:
        instruction = 'stop'
    elif abs(angle_diff) < 30:  # Within 5 degrees, move forward (maybe lower this value)
        instruction = 'move_forward'
    elif angle_diff > 0:
        instruction = 'rotate_right'
    else:
        instruction = 'rotate_left'

    return instruction


def chariot_instructions():
    global chariots, webots, connectedClients, clientCount

    while True:
        if webots:
            print(f"print all chariots: {chariots}")

            for chariot in chariots:
                try:
                    client_socket = connectedClients[chariot]["client_socket"]

                    # add camera and pathplanning code here
                    real_x, real_y, orientation = chariots[chariot]["coordinate"]
                    target_x = webots[str(chariots[chariot]["camera_id"])]["x"]
                    target_y = webots[str(chariots[chariot]["camera_id"])]["y"]

                    instr = get_instruction(chariots[chariot]["camera_id"], target_x, target_y, real_x, real_y, orientation)

                    if not "instr" in chariots[chariot].keys() or chariots[chariot]["instr"] != instr:
                        chariots[chariot]["instr"] = instr

                        payload_send = {
                            "instruction": instr
                            # "instruction": "turn_left"  #instr
                            # "instruction": "turn_right"
                            # "instruction": "move"
                            # "instruction": "stop"
                            # "instruction": "led_on"
                        }

                        try:
                            # stuur je alle instructies naar alle robots? de robot zelf weet niet welk id die heeft?
                            client_socket.sendall(json.dumps(payload_send).encode("ascii"))
                            printings = chariots[chariot]["camera_id"]

                            if instr == "move_forward":
                                print(f"{printings}, \t instruction send: {Fore.GREEN}{payload_send}{Style.RESET_ALL}")
                            elif instr == "rotate_left":
                                print(f"{printings}, \t instruction send: {Fore.YELLOW}{payload_send}{Style.RESET_ALL}")
                            elif instr == "rotate_right":
                                print(f"{printings}, \t instruction send: {Fore.BLUE}{payload_send}{Style.RESET_ALL}")
                            elif instr == "stop":
                                print(f"{printings}, \t instruction send: {Fore.RED}{payload_send}{Style.RESET_ALL}")

                        except:
                            print(f"nothing sent, connection lost with {chariot}")
                            chariots.pop(chariot)
                            connectedClients.pop(chariot)

                            clientCount -= 1
                            print(clientCount, " clients connected")
                            break
                except Exception as e:
                    print(f"chariot_instructions something went wrong {chariot} {e}")
        sleep(0.5)


def camera():
    global chariots

    while True:        
        chariot_coordinates = process_frame_and_return_chariots()

        if chariots and len(chariots) <= len(chariot_coordinates):
            i = 0

            for chariot in chariots:
                chariots[chariot]["coordinate"] = chariot_coordinates[i]
                chariots[chariot]["camera_id"] = i
                i += 1
        sleep(0.1)

def receiving(client_socket, client_address, client_id):
    global webots, chariots

    while True:
        # print(f"{client_id}, trying to receive")

        try:
            payload_json =  json.loads(client_socket.recv(1024).decode())

            if payload_json["type"] == "chariot":
                chariots[client_id] = payload_json
                print("succes")
                return
            
            webots = payload_json
            print(payload_json)
        except BaseException as e:
            print(f"{client_id}, something went wrong, {e}")
            return
        except:
            print(f"{client_id}, no data received")

        sleep(0.01)


def main():
    global connectedClients, clientCount

    print("start chariot_instructions thread")
    t = threading.Thread(
        target=chariot_instructions,
        args=(),
    )
    t.start()

    print("start camera thread")
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


        id = randint(0,100)

        while id in connectedClients:
            id = randint(1, 100)

        connectedClients[id] = {
            "client_socket": client_socket,
            "client_address": client_address
        }

        t = threading.Thread(
            target=receiving,
            args=(
                client_socket,
                client_address,
                id
            ),
        )
        t.start()

        print(clientCount, " clients connected")

main()
