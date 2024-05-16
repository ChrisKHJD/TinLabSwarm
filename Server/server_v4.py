import socket
HOST = 
PORT =

connectedClients = {} #id, ip, port
robots = {} #id, location, direction, last message time

async def main():
    print("start server")
    s = socket.create_server((HOST, PORT))
    s.listen()