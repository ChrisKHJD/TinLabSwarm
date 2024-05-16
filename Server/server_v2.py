import socket
import threading
import json
from datetime import datetime
from time import sleep

HOST = "145.137.54.45"
PORT = 8000

print("host: ", HOST)
print("port: ", PORT)

connectedClients = {}
data = {}

program_run = False

def webots_receiving(client_socket, address):
    print("start webots receiver")

    global connectedClients, data

    connectedClients[address] = client_socket

    try:
        while True:
            print("trying to receive")
            data = json.loads(client_socket.recv(1024).decode)

            print(f"\t{data}")
    finally:
        connectedClients.pop(address)

        print(f"webots disconnected with address {address}")


def chariot_instructions(connection, address):
    print("start robot_instruction")

    global connectedClients, data

    while True:
        print("trying to send")
        payload_sent = {
            "id": 1,
            "time": datetime.now().strftime("%H:%M:%S"),
            "next_position": (0, 0),
        }
        try:
            connection.sendall(json.dumps(payload_sent).encode("ascii"))
            print("\tdata sent")
        except:
            print("\tnothing sent, connection lost")
            break

        sleep(0.1)

    connectedClients.pop(address)

def main():
    print("start server")
    s = socket.create_server((HOST, PORT))
    s.listen()

    client_socket, address = s.accept()
    print(f"connection accepted from {address}")

    t = threading.Thread(
        target=webots_receiving,
        args=(
            client_socket,
            address,
        ),
    )
    t.start()

    while True:
        client_socket, address = s.accept()
        clientCount += 1
        print("connection accepted from ", address)

        t = threading.Thread(
            target=chariot_instructions,
            args=(
                client_socket,
                address,
            ),
        )
        t.start()

        print(clientCount, " clients connected")

main()