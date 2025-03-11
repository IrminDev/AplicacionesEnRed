#!/usr/bin python3

import socket
import os

HOST = os.environ.get("HOST", "localhost")  # Direccion de la interfaz de loopback estándar (localhost)
PORT = int(os.environ.get("PORT", 65432))  # Puerto que usa el cliente  (los puertos sin provilegios son > 1023)
buffer_size = int(os.environ.get("BUFFER_SIZE", 1024))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as TCPClientSocket:
    TCPClientSocket.connect((HOST, PORT))
    print("Enviando mensaje...")
    TCPClientSocket.send("Preparing for a new file".encode())
    data = TCPClientSocket.recv(buffer_size)
    print("Connection stablished: ", str(data))
    filePath = os.path.join(os.path.dirname(__file__), "MobyDick.txt")
    with open(filePath, 'r') as file:
        print("Connection stablished: ", str(data))
        block = file.read(buffer_size)
        while(block != ""):
            TCPClientSocket.sendall(str.encode(block))
            block = file.read(buffer_size)
            data = TCPClientSocket.recv(buffer_size)
        block = "$$$EOF$$$"
        TCPClientSocket.sendall(str.encode(block))
        data = TCPClientSocket.recv(buffer_size)
        print("Recibido,", str(data), " de", TCPClientSocket.getpeername())
    print("Finihed")
    TCPClientSocket.close()