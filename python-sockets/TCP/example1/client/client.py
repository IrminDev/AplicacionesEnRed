#!/usr/bin python3

import socket
import os

HOST = os.environ.get("HOST", "")  # Direccion de la interfaz de loopback estándar (localhost)
PORT = int(os.environ.get("PORT", 65432))  # Puerto que usa el cliente  (los puertos sin provilegios son > 1023)
buffer_size = int(os.environ.get("BUFFER_SIZE", 1024))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as TCPClientSocket:
    TCPClientSocket.connect((HOST, PORT))
    print("Enviando mensaje...")
    TCPClientSocket.sendall(b"Hola servidor TCP ")
    print("Esperando una respuesta...")
    data = TCPClientSocket.recv(buffer_size)
    print("Recibido,", repr(data), " de", TCPClientSocket.getpeername())
