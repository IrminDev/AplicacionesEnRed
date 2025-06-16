#!/usr/bin python3
import socket
import os
import threading

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", 65432))
buffer_size = int(os.environ.get("BUFFER_SIZE", 1024))

connections_lock = threading.Lock()
threads = []
connections = []
client_names = {} 
barrier = threading.Barrier(5)

def broadcast(message, sender_conn):
    with connections_lock:
        for client in connections:
            if client != sender_conn:
                try:
                    sender_name = client_names.get(sender_conn, "Unknown")
                    formatted_message = f"{sender_name}: {message.decode()}".encode()
                    client.sendall(formatted_message)
                except:
                    client.close()
                    if client in connections:
                        connections.remove(client)

def handle_client(Client_conn, Client_addr):
    with Client_conn:
        print(f"Conectado a {Client_addr}")
        Client_conn.sendall(b"Please enter your name: ")
        name_data = Client_conn.recv(buffer_size)
        if name_data:
            client_names[Client_conn] = name_data.decode().strip()
            welcome_message = f"*** {client_names[Client_conn]} has joined the chat ***".encode()
            broadcast(welcome_message, Client_conn)
            Client_conn.sendall(b"Welcome to the chat room! Type your messages.\n")
        
        while True:
            try:
                data = Client_conn.recv(buffer_size)
                if not data:
                    break
                print(f"Received from {client_names.get(Client_conn, 'Unknown')}: {data.decode()}")
                
                broadcast(data, Client_conn)
            except Exception as e:
                print(f"Error handling client {Client_addr}: {e}")
                break
        
        
        if Client_conn in client_names:
            disconnect_message = f"*** {client_names[Client_conn]} has left the chat ***".encode()
            broadcast(disconnect_message, Client_conn)
            del client_names[Client_conn]
        
        with connections_lock:
            if Client_conn in connections:
                connections.remove(Client_conn)
        
        print(f"Conexión cerrada con {Client_addr}")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as TCPServerSocket:
        TCPServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        TCPServerSocket.bind((HOST, PORT))
        TCPServerSocket.listen(5)
        print(f"Chat server running on {HOST}:{PORT}")
        print("El servidor TCP está disponible y en espera de solicitudes")

        try:
            while True:
                Client_conn, Client_addr = TCPServerSocket.accept()
                with connections_lock:
                    connections.append(Client_conn)
                
                client_thread = threading.Thread(target=handle_client, args=(Client_conn, Client_addr))
                threads.append(client_thread)
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            # Close all connections
            with connections_lock:
                for conn in connections:
                    try:
                        conn.close()
                    except:
                        pass

if __name__ == "__main__":
    main()