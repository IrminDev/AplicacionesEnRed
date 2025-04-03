#!/usr/bin python3
import socket
import os
import threading

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", 65432))
buffer_size = int(os.environ.get("BUFFER_SIZE", 1024))

threads = []
connections = []

def handle_client(Client_conn, Client_addr):
    with Client_conn:
        print("Conectado a", Client_addr)
        while True:
            print("Esperando a recibir datos... ")
            data = Client_conn.recv(buffer_size)
            print("Recibido,", data, "   de ", Client_addr)
            if not data:
                break
            print("Enviando respuesta a", Client_addr)
            Client_conn.sendall(data)
    print("Conexión cerrada con", Client_addr)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as TCPServerSocket:
    TCPServerSocket.bind((HOST, PORT))
    TCPServerSocket.listen(5)
    print("El servidor TCP está disponible y en espera de solicitudes")

    while True:
        Client_conn, Client_addr = TCPServerSocket.accept()
        Client_conn.setblocking(0)
        connections.append(Client_conn)
        client_thread = threading.Thread(target=handle_client, args=(Client_conn, Client_addr))
        threads.append(client_thread)
        client_thread.start()