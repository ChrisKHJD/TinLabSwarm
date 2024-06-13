import socket
import threading
import json
import math
from datetime import datetime
from time import sleep
from random import randint
from colorama import Fore, Style

from Junk.RobotTrackingCamera import getchariots

# HOST = "145.24.223.115"
# PORT = 8000
HOST = "145.137.54.68"
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
def calculate_angle(x1, y1, x2, y2):
    calculated_angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    # if calculated_angle < 0:
    #     return 360 + calculated_angle
    # else:
    return calculated_angle


# Calculate the smallest difference between two angles.
def angle_difference(angle1, angle2):
    return (angle1 - angle2 + 180) % 360 - 180


# Calculate the Euclidean distance between two points.
def distance(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


# Generate movement instructions for robot to reach target. test threshold value
def get_instruction(robot_id, target_x, target_y, real_x, real_y, orientation, threshold=15):
    instruction = ""

    target_angle = calculate_angle(real_x, real_y, target_x, target_y)
    angle_diff = angle_difference(target_angle, orientation)
    print(f"target angle: {target_angle}, orentation: {orientation}, difference {target_angle - orientation}")
    print(f"distance from destination {distance(real_x, real_y, target_x, target_y)}")

    if distance(real_x, real_y, target_x, target_y) <= threshold:
        instruction = 'stop'
    elif abs(angle_diff) < 30:  # Within 5 degrees, move forward (maybe lower this value)
        instruction = 'move_forward'
    elif angle_diff > 0:
        instruction = 'rotate_left'
    else:
        instruction = 'rotate_right'

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

                    instr = get_instruction(chariot, target_x, target_y, real_x, real_y, orientation)

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
                        chariot_print = chariots[chariot]["camera_id"]

                        if instr == "move_forward":
                            print(f"{chariot_print}, instruction send: {Fore.GREEN}{payload_send}{Style.RESET_ALL}, time: {datetime.now()}")
                        elif instr == "rotate_left":
                            print(f"{chariot_print}, instruction send: {Fore.YELLOW}{payload_send}{Style.RESET_ALL}, time: {datetime.now()}")
                        elif instr == "rotate_right":
                            print(f"{chariot_print}, instruction send: {Fore.BLUE}{payload_send}{Style.RESET_ALL}, time: {datetime.now()}")
                        elif instr == "stop":
                            print(f"{chariot_print}, instruction send: {Fore.RED}{payload_send}{Style.RESET_ALL}, time: {datetime.now()}")

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
        chariot_coordinates = getchariots()

        if chariots and len(chariots) <= len(chariot_coordinates):
            i = 0

            for chariot in chariots:
                chariots[chariot]["coordinate"] = chariot_coordinates[i]
                chariots[chariot]["camera_id"] = i
                i += 1
        # sleep(0.1)

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

        sleep(0.1)


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
