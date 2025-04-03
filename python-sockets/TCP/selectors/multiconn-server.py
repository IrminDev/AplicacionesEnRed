#!/usr/bin/env python3
#
import sys
import socket
import selectors
import types
import logging
import time
import queue

sel = selectors.DefaultSelector()

# Create a message queue for each client
message_queues = {}

def accept(sock_a, mask):
    sock_conn, addr = sock_a.accept()  # Should be ready
    print('aceptado', sock_conn, ' de', addr)
    sock_conn.setblocking(False)
    
    # Create a new message queue for this connection
    message_queues[sock_conn] = queue.Queue()
    
    # Register for both read and write events
    sel.register(sock_conn, selectors.EVENT_READ | selectors.EVENT_WRITE, read_write)

def read_write(sock_c, mask):
    if mask & selectors.EVENT_READ:
        data = sock_c.recv(1024)
        if data:
            print('recibido', repr(data), 'a', sock_c)
            message_queues[sock_c].put(data) # Agrega el mensaje a la cola del cliente para enviar
        else:
            print('cerrando', sock_c)
            sel.unregister(sock_c)
            sock_c.close()
            del message_queues[sock_c]
            
    if mask & selectors.EVENT_WRITE:
        if sock_c in message_queues:
            try:
                # Manda todos los mensajes hasta que la cola del socket esté vacía
                if not message_queues[sock_c].empty():
                    next_msg = message_queues[sock_c].get_nowait()
                    print('enviando', repr(next_msg), 'a', sock_c)
                    sock_c.sendall(next_msg)
            except Exception as e:
                print(f"Error sending data: {e}")
                sel.unregister(sock_c)
                sock_c.close()
                del message_queues[sock_c]

with socket.socket() as sock_accept:
    sock_accept.bind(('localhost', 12345))
    sock_accept.listen(100)
    sock_accept.setblocking(False)
    sel.register(sock_accept, selectors.EVENT_READ, accept)
    
    while True:
        print("Esperando evento...")
        # Timeout to allow periodic tasks
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)