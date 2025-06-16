import socket
import argparse
import os
import time
import os

DEFAULT_HOST = "localhost"
DEFAULT_USER = "ftpuser"
DEFAULT_PASSWORD = "clave123"

class FTPClient:
    def __init__(self, host, port = 21):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        response = self.receive()
        print(response)
        return response.startswith("220")
    
    def send_command(self, command):
        self.socket.sendall((command + "\r\n").encode())
    
    def receive(self):
        response = b""
        while True:
            data = self.socket.recv(4098)
            response += data
            if b"\r\n" in data:
                break
        return response.decode().strip()

    def login(self, user, password):
        self.send_command(f"USER {user}")
        response = self.receive()
        print(response)
        if not response.startswith("331"):
            return False
        self.send_command(f"PASS {password}")
        response = self.receive()
        print(response)
        return response.startswith("230")
    
    def recv_all(self, sock):
        sock.settimeout(5)
        data = b""
        try:
            while True:
                part = sock.recv(4096)
                if not part:
                    break
                data += part
        except socket.timeout:
            pass
        return data

    def pasv(self):
        self.send_command("PASV")
        response = self.receive()
        print(response)
        return response

    def list_files(self):
        response = self.pasv()
        if not response.startswith("227"):
            return []
        data_host, data_port = self.parse_pasv_response(response)
        data_sock = socket.create_connection((data_host, data_port))
        self.send_command("NLST")
        response = self.receive()
        print(response)
        if not response.startswith("150"):
            print("Server rejected read files")
            data_sock.close()
            return []
        list = self.recv_all(data_sock).decode().strip().splitlines()
        data_sock.close()
        response = self.receive()
        print(response)
        if not response.startswith("226"):
            print("There was a problem while reading the directory or with the socket")
            return []
        return list

    def download_file(self, filename):
        response = self.pasv()
        if not response.startswith("227"):
            return
        data_host, data_port = self.parse_pasv_response(response)
        data_sock = socket.create_connection((data_host, data_port))
        self.send_command(f"RETR {filename}")
        response = self.receive()
        print(response)
        if response.startswith("550"):
            print("The file doesn't exist in the server.")
            data_sock.close()
            return
        if not response.startswith("150"):
            print("Server rejected file download.")
            data_sock.close()
            return
        local_path = f"Downloaded_{filename}"
        with open(local_path, "wb") as f:
            f.write(self.recv_all(data_sock))
        data_sock.close()
        print(f"Downloaded '{filename}' → {local_path}")
        response = self.receive()
        print(response)

    def upload_file(self, local_path, remote_name = None):
        if not os.path.isfile(local_path):
            print("File does not exist: ", local_path)
            return

        remote_name = remote_name or os.path.basename(local_path)

        response = self.pasv()
        if not response.startswith("227"):
            return
        data_host, data_port = self.parse_pasv_response(response)
        data_sock = socket.create_connection((data_host, data_port))
        self.send_command(f"STOR {remote_name}")
        response = self.receive()
        print(response)
        if not response.startswith("150"):
            print("Server rejected file upload.")
            data_sock.close()
            return

        with open(local_path, "rb") as f:
            data_sock.sendfile(f)
        data_sock.close()
        print(f"Uploaded '{local_path}' as '{remote_name}'")
        response = self.receive()
        print(response)

    def parse_pasv_response(self, response):
        ip_component = response.split('(')[1].split(')')[0]
        ip_nums = ip_component.split(',')
        data_host = '.'.join(ip_nums[:4])
        data_port = (int(ip_nums[4]) << 8) + int(ip_nums[5])
        return data_host, data_port

    def disconnect(self):
        self.send_command('QUIT')
        response = self.receive()
        print(response)
        self.socket.close()


def main():
    parser = argparse.ArgumentParser(description='Tic Tac Toe Server')
    parser.add_argument('--host', type = str, default = DEFAULT_HOST, help = 'Server host (default: localhost)')
    parser.add_argument('--user', type = str, default= DEFAULT_USER, help = 'FTP User (default: ftpuser)')
    parser.add_argument('--password', type = str, default = DEFAULT_PASSWORD, help = 'Password of players (default: clave123)')
    args = parser.parse_args()
    ftp_client = FTPClient(args.host)
    if ftp_client.connect():
        if ftp_client.login(args.user, args.password):
            while True:
                print("Operations: ")
                print("1. List files")
                print("2. Download file")
                print("3. Upload file")
                print("4. Exit")
                print("Select an option")
                option = int(input())
                if option == 4:
                    ftp_client.disconnect()
                    break
                if option == 1:
                    list = ftp_client.list_files()
                    print(list)
                    time.sleep(2)
                elif option == 2:
                    print("Enter the filename")
                    filename = input()
                    ftp_client.download_file(filename)
                else:
                    print("Enter the path of the file")
                    path = input()
                    print("Enter the name of the file as it will be saved on the server")
                    name = input()
                    ftp_client.upload_file(path, name)


        else:
            print("Login failed")
    else:
        print("Connection Failed")


if __name__ == "__main__":
    main()