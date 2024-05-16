import socket
import threading
import json
from datetime import datetime
from time import sleep

HOST = "145.24.223.115"
PORT = 8000

connectedClients = {} #id, ip, port
robots = {} #id, location, direction, last message time

async def client_init(client_socket, client_address):
    global robots

    while True:
        print("trying to send")

        payload_sent = {
            "id": 1,
            "time": datetime.now().strftime("%H:%M:%S"),
            "next_position": (0, 0),
        }
        try:
            await client_socket.sendall(json.dumps(payload_sent).encode("ascii"))
            print("\tdata sent")
        except:
            print("\tnothing sent, connection lost")
            break

        sleep(0.1)

async def main():
    print("start server")
    s = socket.create_server((HOST, PORT))
    s.listen()

    while True:
        client_socket, client_address = s.accept()
        clientCount += 1
        print("connection accepted from ", client_address)

        json.loads(await client_socket.recv(1048))

        t = threading.Thread(
            target=client_init,
            args=(
                client_socket,
                client_address,
            ),
        )
        t.start()

        print(clientCount, " clients connected")

main()