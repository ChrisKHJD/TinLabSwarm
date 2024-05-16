import socket
import threading
import json
from datetime import datetime
from time import sleep

HOST = "145.137.54.45"
PORT = 8000

print("host: ", HOST)
print("port: ", PORT)

clientCount = 0
data = {}

program_run = False


def robot_instructions(connection, address):
    print("start robot_instruction")

    global clientCount, data
    while True:
        print("trying to receive")
        try:
            payload_received = json.loads(connection.recv(1024).decode())

            id = payload_received["id"]

            data[id] = payload_received

            print("\t", payload_received)
        except:
            print("\tno data received")

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

    clientCount -= 1
    data.pop(id)
    if clientCount == 0:
        print("All clients disconnected; resetting")
        data = {}
        program_run = False
        if not data:
            print("incoming is empty")


print("start server")
s = socket.create_server((HOST, PORT))
s.listen()

while True:
    connection, address = s.accept()
    clientCount += 1
    print("connection accepted from ", address)

    t = threading.Thread(
        target=robot_instructions,
        args=(
            connection,
            address,
        ),
    )
    t.start()

    print(clientCount, " clients connected")
    program_run = True
