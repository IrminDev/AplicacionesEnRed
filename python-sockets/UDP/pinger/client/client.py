from socket import *
import os
import time

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", 12000))

clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(1)

pings = 0;

maxTime = 0;

minTime = 100000000;

for i in range(10):
    try:
        clientSocket.sendto(str.encode("ping"), (HOST, PORT))
        start = time.time();
        response = clientSocket.recvfrom(1024);
        end = time.time();
        print("Message received: {}".format(response[0]))
        print("RTT: ", round((end-start)*1000, 3), " ms")
        maxTime = max(maxTime, (end-start))
        minTime = min(minTime, (end-start))
        pings = pings+1
    except timeout:
        print("Request timeout")

print("Pings received: ", pings)
print("Lost messages: ", 10-pings)
print("Message rate: ", (pings*10), "%")
print("Max time: ", round(maxTime*1000, 4), " ms")
print("Min time: ", round(minTime*1000, 4), " ms")