import socket
import json
from datetime import datetime
from time import sleep

HOST = "145.24.223.115"
PORT = 8000

s = socket.socket()

def send():
    print("method: send")
    try:
        payload = {
            1: {
                "current_position": (0, 0)
            },
            2: {
                "current_position": (0, 0)
            },
            3: {
                "current_position": (0, 0)
            },
            4: {
                "current_position": (0, 0)
            },
            "time_sent": datetime.now().strftime("%H:%cM:%S")

        }
        s.sendall(json.dumps(payload).encode("ascii"))
        print("sent")
    except:
        print("nothing sent")


def receive():
    print("method: receive")
    try:
        incoming = s.recv(1024).decode()
        print("\t", incoming)
    except:
        print("\tno incoming")


def init():
    print("startup")

    try:
        s.connect((HOST, PORT))
        print("connected")
        s.settimeout(0.1)
    except:
        print("connection refused")
        exit()


def main():
    while True:
        send()
        # receive()
        sleep(0.5)

init()
main()
