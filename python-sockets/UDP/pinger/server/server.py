import random 
from socket import * 
import os

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", 12000))
# Crear un socket UDP 
serverSocket = socket(AF_INET, SOCK_DGRAM) 
# Asignar dirección IP y número de puerto al socket 
serverSocket.bind((HOST, PORT)) 
while True: 
    rand = random.randint(0, 10) 
    message, address = serverSocket.recvfrom(1024) 
    message = message.upper() 
    if rand < 4: 
        continue 
    # De lo contrario, el servidor responde 
    serverSocket.sendto(message, address)