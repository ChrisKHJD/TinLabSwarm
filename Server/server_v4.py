import socket
import threading
import json
from datetime import datetime
from time import sleep

HOST = "145.24.223.115"
PORT = 8000
# HOST = "145.137.54.196"
# PORT = 8000

connectedClients = {} #id, client_socket, client_address
webots = {} #id, location, last message time
chariots = {} #id, location, direction, last message time

def chariot_instructions():
    global chariots

    while True:
        for chariot in chariots:
            print(chariots[chariot])

            client_socket = connectedClients[chariot]["client_socket"]

            #add camera and pathplanning code here

            payload_send = {
                "instruction": "turn_left"
                # "instruction": "turn_right"
                # "instruction": "move"
            }

            try:
                client_socket.sendall(json.dumps(payload_send).encode("ascii"))
                print("\tdata sent")
            except:
                print("\tnothing sent, connection lost")
                break

        sleep(0.1)

def camera():
    while True:
        print("hello")
        sleep(50)

def receiving(client_socket, client_address, client_id):
    global webots, chariots

    while True:
        print(f"{client_id}, trying to receive")

        try:
            # webots = json.loads(client_socket.recv(1024).decode())
            # print(json.loads(client_socket.recv(1024).decode()))
            print(client_socket.recv(1024).decode())

            # if payload_received["type"] == "webot":
            #     webots[client_id] = payload_received
            # elif payload_received["type"] == "chariot":
            #     chariots[client_id] = payload_received

            # webots = payload_received

            print(webots)
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