#!/usr/bin python3

import socket
import os
import random
import time

HOST = os.environ.get("HOST", "localhost")  # Direccion de la interfaz de loopback estándar (localhost)
PORT = int(os.environ.get("PORT", 65432))  # Puerto que usa el cliente  (los puertos sin provilegios son > 1023)
buffer_size = int(os.environ.get("BUFFER_SIZE", 1024))

messages = [b"Mensaje 1", b"Mensaje 2", b"Mensaje 3", b"Mensaje 4", b"Mensaje 5"]

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as TCPClientSocket:
    TCPClientSocket.connect((HOST, PORT))
    print("Enviando mensaje...")
    while True:
        message = random.choice(messages)
        TCPClientSocket.send(message)
        data = TCPClientSocket.recv(buffer_size)
        print("Recibido,", data, " de", TCPClientSocket.getpeername())
        time.sleep(3)
