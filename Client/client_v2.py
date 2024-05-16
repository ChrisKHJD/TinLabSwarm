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
            "id": 1,
            "time": datetime.now().strftime("%H:%cM:%S"),
            "current_position": (0, 0)
        }
        s.sendall(json.dumps(payload).encode("ascii"))
        print("\tsent")
    except:
        print("\tnothing sent")


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
        receive()

init()
main()
