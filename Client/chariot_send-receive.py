import socket
import json
from datetime import datetime
from time import sleep
from time import time

# HOST = "145.24.223.115"
# PORT = 8000
HOST = "145.137.54.196"
PORT = 8000

s = socket.socket()


def send():
    print("method: send")
    try:
        payload = {"type": "chariot", "time_sent": datetime.now().strftime("%H:%cM:%S")}
        s.sendall(json.dumps(payload).encode("ascii"))
        print(f"sent payload, {payload}")
    except:
        print("nothing sent")


def receive():
    print("method: receive")
    try:
        incoming = s.recv(1024).decode()
        print("\t", incoming)
        return True
    except:
        print("\tno incoming")
        return False


def init():
    print("startup")

    try:
        s.connect((HOST, PORT))
        print("connected")
        s.settimeout(0.1)
    except:
        print("connection refused")
        exit()

    lastTime = time()

    while True:
        try:
            if time() - lastTime > 1:
                send()
                lastTime = time()

            if receive():
                return
        except:
            print("something went wrong")


def main():
    while True:
        receive()
        sleep(0.5)


init()
main()
