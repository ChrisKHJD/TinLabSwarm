import socket
import threading
import json
import math
import time
from datetime import datetime
from time import sleep
from random import randint
from colorama import Fore, Style

from newRobotTracking import process_frame_and_return_chariots, get_camera_and_set_capture

# HOST = "145.24.223.115"
# PORT = 8000
HOST = "145.24.243.16"
PORT = 8000
lock = threading.Lock()  # For synchronizing access to shared data

clientCount = 0

connectedClients = {}  #id, client_socket, client_address
webots = {}  #id, location, last message time
chariots = {} #id, location, direction, last message time

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
def get_instruction(camera_id, target_x, target_y, real_x, real_y, orientation, threshold=20):
    instruction = ""
    angle_diff = angle_to_target(real_x, real_y, target_x, target_y, orientation)
    print(f"{camera_id}: \t {Fore.CYAN}angle_diff: {angle_diff}{Style.RESET_ALL}, {Fore.WHITE}orientation: {orientation}{Style.RESET_ALL}, {Fore.MAGENTA}distance: {distance(real_x, real_y, target_x, target_y)}{Style.RESET_ALL}")

    if distance(real_x, real_y, target_x, target_y) <= threshold:
        instruction = 'stop'
    elif abs(angle_diff) < 15:  # Within 5 degrees, move forward (maybe lower this value)
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

            for chariot_id in chariots:
                try:
                    with lock:
                        client_socket = connectedClients[chariot_id]["client_socket"]

                        real_x, real_y, orientation = chariots[chariot_id]["coordinate"]
                        target_x = webots[str(chariots[chariot_id]["camera_id"])]["x"]
                        target_y = webots[str(chariots[chariot_id]["camera_id"])]["y"]

                        instr = get_instruction(chariots[chariot_id]["camera_id"], target_x, target_y, real_x, real_y, orientation)

                        if not "instr" in chariots[chariot_id].keys() or chariots[chariot_id]["instr"] != instr:
                            chariots[chariot_id]["instr"] = instr

                            payload_send = {
                                "instruction": instr
                            }

                            try:
                                client_socket.sendall(json.dumps(payload_send).encode("ascii"))

                                # match instr:
                                #     case "move_forward":
                                #         print(f"{chariots[chariot_id]['camera_id']}, \t instruction send: {Fore.GREEN}{payload_send}{Style.RESET_ALL}")
                                #         break
                                #     case "rotate_left":
                                #         print(f"{chariots[chariot_id]['camera_id']}, \t instruction send: {Fore.YELLOW}{payload_send}{Style.RESET_ALL}")
                                #         break
                                #     case "rotate_right":
                                #         print(f"{chariots[chariot_id]['camera_id']}, \t instruction send: {Fore.BLUE}{payload_send}{Style.RESET_ALL}")
                                #         break
                                #     case "stop":
                                #         print(f"{chariots[chariot_id]['camera_id']}, \t instruction send: {Fore.RED}{payload_send}{Style.RESET_ALL}")
                                #         break

                                if instr == "move_forward":
                                    print(f"{chariots[chariot_id]['camera_id']}, \t instruction send: {Fore.GREEN}{payload_send}{Style.RESET_ALL}")
                                elif instr == "rotate_left":
                                    print(f"{chariots[chariot_id]['camera_id']}, \t instruction send: {Fore.YELLOW}{payload_send}{Style.RESET_ALL}")
                                elif instr == "rotate_right":
                                    print(f"{chariots[chariot_id]['camera_id']}, \t instruction send: {Fore.BLUE}{payload_send}{Style.RESET_ALL}")
                                elif instr == "stop":
                                    print(f"{chariots[chariot_id]['camera_id']}, \t instruction send: {Fore.RED}{payload_send}{Style.RESET_ALL}")

                            except:
                                print(f"nothing sent, connection lost with {chariot_id}")
                                chariots.pop(chariot_id)
                                connectedClients.pop(chariot_id)

                                clientCount -= 1
                                print(clientCount, " clients connected")
                                break
                except Exception as e:
                    print(f"chariot_instructions something went wrong {chariot_id} {e}")
        sleep(0.2)


def camera():
    global chariots, webots

    while True:
        #process frame and get chariots
        chariot_coordinates = process_frame_and_return_chariots()

        with lock:
            if chariots:
                for chariot_id in chariots.keys():
                    chariots[chariot_id]["coordinate"] = chariot_coordinates[chariots[chariot_id]["camera_id"]]
        # means fetching 5 frames each second
        sleep(0.2)

def receiving(client_socket, client_address, client_id):
    global webots, chariots

    while True:
        try:
            payload_json = json.loads(client_socket.recv(1024).decode())
            with lock:
                if payload_json["type"] == "chariot":
                    chariots[client_id] = payload_json
                    chariots[client_id]["camera_id"] = len(chariots) - 1
                    print("succes")
                    return
            
                webots = payload_json
                print(payload_json)
        except json.JSONDecodeError as e:
            print(f"{client_id}, JSON decode error, {e}")
            return
        except socket.error as e:
            print(f"{client_id}, socket error, {e}")
            return
        except:
            print(f"{client_id}, no data received")

        sleep(0.01)


def main():
    global connectedClients, clientCount

    get_camera_and_set_capture()
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
        print(f"connection accepted from {client_address}, ")


        id = randint(0,100)

        while id in connectedClients:
            id = randint(1, 100)

        with lock:
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
