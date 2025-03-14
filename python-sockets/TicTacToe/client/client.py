#!/usr/bin python3

import socket
import os

buffer_size = int(os.environ.get("BUFFER_SIZE", 1024))

def generateGrid(n):
    grid = []
    for i in range(n):
        row = []
        for j in range(n):
            row.append(" ")
        grid.append(row)
    return grid

def printGrid(grid):
    for row in grid:
        print(row)

print("Enter the host and port of the server: ")
HOST = input("Host: ")
PORT = int(input("Port: "))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as TCPClientSocket:
    TCPClientSocket.connect((HOST, PORT))
    print("Connecting to server...")
    TCPClientSocket.sendall(b"Play request")
    print("Request sent")
    data = TCPClientSocket.recv(buffer_size)
    n = int(data.decode())
    grid = generateGrid(n)
    printGrid(grid)
    print("Your turn: ")
    row = int(input("Enter row: "))
    col = int(input("Enter col: "))
    TCPClientSocket.sendall(f"{row}|{col}".encode())
    data = TCPClientSocket.recv(buffer_size)
    while (data == b"Invalid move"):
        print("Invalid move")
        row = int(input("Enter row: "))
        col = int(input("Enter col: "))
        TCPClientSocket.sendall(f"{row}|{col}".encode())
        data =  TCPClientSocket.recv(buffer_size)
    grid[row][col] = "X"
    print("Waiting for opponent's move...")
    while True:
        data = TCPClientSocket.recv(buffer_size)
        if not data:
            break
        if data == b"You win":
            printGrid(grid)
            print("You win")
            break
        if "Game over" in data.decode():
            if "Tie" in data.decode():
                print("Game over: Tie")
                break
            row, col = map(int, data.decode().split(":")[1].split("|"))
            grid[row][col] = "O"
            printGrid(grid)
            print("Game over: Tie")
            break
        if "You lose" in data.decode():
            row, col = map(int, data.decode().split(":")[1].split("|"))
            grid[row][col] = "O"
            printGrid(grid)
            print("You lose")
            break
        row, col = map(int, data.decode().split("|"))
        grid[row][col] = "O"
        printGrid(grid)
        print("Your turn: ")
        row = int(input("Enter row: "))
        col = int(input("Enter col: "))
        TCPClientSocket.sendall(f"{row}|{col}".encode())
        data = TCPClientSocket.recv(buffer_size)
        while (data == b"Invalid move"):
            print("Invalid move")
            row = int(input("Enter row: "))
            col = int(input("Enter col: "))
            TCPClientSocket.sendall(f"{row}|{col}".encode())
            data =  TCPClientSocket.recv(buffer_size)
        grid[row][col] = "X"
    TCPClientSocket.close()