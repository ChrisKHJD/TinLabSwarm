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

def client_init(client_socket, client_address):
    data = {}

    print(f"new connection from {client_address}")

    try:
        while True:
            data = json.loads(client_socket.recv(1024).decode)

            if data["category"] == "webots":
                t = threading.Thread(
                    target=client_init,
                    args=(
                        client_socket,
                        client_address,
                    ),
                )
                t.start()
                break
            if data["category"] == "chariot":
                t = threading.Thread(
                    target=client_init,
                    args=(
                        client_socket,
                        client_address,
                    ),
                )
                t.start()
                break
            if data["category"] == "camera":
                t = threading.Thread(
                    target=client_init,
                    args=(
                        client_socket,
                        client_address,
                    ),
                )
                t.start()
                break
    finally:
        client_socket.sendall(data["time"])    
    

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