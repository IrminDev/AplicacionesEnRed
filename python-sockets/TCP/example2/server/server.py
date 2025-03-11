#!/usr/bin python3
import socket
import os

HOST = os.environ.get("HOST", "localhost")  # Direccion de la interfaz de loopback estándar (localhost)
PORT = int(os.environ.get("PORT", 65432))  # Puerto que usa el cliente  (los puertos sin provilegios son > 1023)
buffer_size = int(os.environ.get("BUFFER_SIZE", 1024))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as TCPServerSocket:
    TCPServerSocket.bind((HOST, PORT))
    TCPServerSocket.listen()
    print("The server is available and waiting for requests")
    Client_conn, Client_addr = TCPServerSocket.accept()
    with Client_conn:
        print("Connected to: ", Client_addr)
        data = Client_conn.recv(buffer_size)
        print("Connection stablished: ", data.decode(), "   de ", Client_addr)
        Client_conn.send("Connection stablished".encode())
        while data:
            data = Client_conn.recv(buffer_size)
            if data == b'$$$EOF$$$':
                break
            print("Recibido,", data.decode(), "   de ", Client_addr)
            if data:
                Client_conn.send("Block received".encode())
        print("Finished: ", data.decode())
    TCPServerSocket.close()