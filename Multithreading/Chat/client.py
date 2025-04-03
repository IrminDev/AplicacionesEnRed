#!/usr/bin python3
import socket
import os
import threading
import sys

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", 65432))
buffer_size = int(os.environ.get("BUFFER_SIZE", 1024))

def receive_messages(sock):
    while True:
        try:
            data = sock.recv(buffer_size)
            if not data:
                print("\nDisconnected from server")
                break
            print(f"\n{data.decode()}")
            print("You: ", end="", flush=True)  # Reprint the input prompt
        except Exception as e:
            print(f"\nError receiving message: {e}")
            break
    
    # If we exit the loop, the connection is closed
    print("\nConnection to server lost.")
    sock.close()
    os._exit(1)  # Force exit the program

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((HOST, PORT))
            print(f"Connected to chat server at {HOST}:{PORT}")
            
            receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
            receive_thread.daemon = True
            receive_thread.start()
            
            initial_prompt = client_socket.recv(buffer_size).decode()
            print(initial_prompt, end="", flush=True)
            
            # Main loop for sending messages
            while True:
                message = input()
                if message.lower() in ['exit', 'quit', 'bye']:
                    break
                
                client_socket.sendall(message.encode())
                print("You: ", end="", flush=True)
                
        except KeyboardInterrupt:
            print("\nExiting...")
        except Exception as e:
            print(f"\nError: {e}")
        finally:
            try:
                # Let the server know we're disconnecting
                client_socket.sendall(b"")
            except:
                pass
            print("Disconnected from server")

if __name__ == "__main__":
    main()