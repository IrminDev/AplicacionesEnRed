import socket
import os
import random

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

def checkCols(grid, player):
    for i in range(len(grid)):
        win = True
        for j in range(len(grid)):
            if grid[j][i] != player:
                win = False
                break
        if win:
            return True
    return False

def checkRows(grid, player):
    for i in range(len(grid)):
        win = True
        for j in range(len(grid)):
            if grid[i][j] != player:
                win = False
                break
        if win:
            return True
    return False

def checkDiagonals(grid, player):
    win = True
    for i in range(len(grid)):
        if grid[i][i] != player:
            win = False
            break
    if win:
        return True
    win = True
    for i in range(len(grid)):
        if grid[i][len(grid) - 1 - i] != player:
            win = False
            break
    return win

def checkWin(grid, player):
    return checkCols(grid, player) or checkRows(grid, player) or checkDiagonals(grid, player)

def checkTie(grid):
    for row in grid:
        for cell in row:
            if cell == " ":
                return False
    return True

print("Enter the host and port of the server: ")
HOST = input("Host: ")
PORT = int(input("Port: "))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as TCPServerSocket:
    TCPServerSocket.bind((HOST, PORT))
    TCPServerSocket.listen()
    print("Waiting for connection...")
    Client_conn, Client_addr = TCPServerSocket.accept()
    with Client_conn:
        print("Connected to", Client_addr)
        data = Client_conn.recv(buffer_size)
        print(data.decode())
        # Generate a random n between 3 and 5
        n = random.randint(3, 6)
        grid = generateGrid(n)
        printGrid(grid)
        player = "O"
        Client_conn.sendall(f"{n}".encode())
        while True:
            print("Waiting for opponent's move...")
            data = Client_conn.recv(buffer_size)
            if not data:
                break
            row, col = map(int, data.decode().split("|"))
            grid[row][col] = "X"
            printGrid(grid)
            if checkWin(grid, "X"):
                Client_conn.sendall(b"You win")
                break
            if checkTie(grid):
                Client_conn.sendall(b"Game over: Tie")
                break
            print("Your turn")
            dummyRow = random.randint(0, n - 1)
            dummyCol = random.randint(0, n - 1)
            while grid[dummyRow][dummyCol] != " ":
                dummyRow = random.randint(0, n - 1)
                dummyCol = random.randint(0, n - 1)
            grid[dummyRow][dummyCol] = "O"
            printGrid(grid)
            if checkWin(grid, "O"):
                Client_conn.sendall(f"You lose: {dummyRow}|{dummyCol}".encode())
                break
            if checkTie(grid):
                Client_conn.sendall(f"Game over: {dummyRow}|{dummyCol}".encode())
                break
            Client_conn.sendall(f"{dummyRow}|{dummyCol}".encode())

