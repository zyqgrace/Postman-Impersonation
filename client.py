import os
import socket
import sys
from dataclasses import dataclass

# Visit https://edstem.org/au/courses/8961/lessons/26522/slides/196175 to get
PERSONAL_ID = 'B03FFA'
PERSONAL_SECRET = '113619c855557bbe68464878e6aea7d3'

def parse_conf_path():
    server_port = None
    send_path = None
    try:
        conf_path = open(sys.argv[1],'r')
        configuration = conf_path.readlines()
        for info in configuration:
            info = info.strip("\r\n")
            if info[0:11] == "server_port":
                server_port = info[12:]
            elif info[0:9] == "send_path":
                send_path = info[10:]
    except FileNotFoundError:
        sys.exit(1)
    if server_port.isnumeric() == False:
        sys.exit(2)
    elif int(server_port) <= 1024:
        sys.exit(2)
    elif send_path == None:
        sys.exit(2)
    send_path = os.path.expanduser(send_path)
    return int(server_port),send_path

def directory_lis(send_path):
    """
    parameter: the send path after parsing example(~/send)
    This will return all the files in alphabetically order
    """
    files = []
    try:
        for file in os.listdir(send_path):
            files.append(send_path+"/"+file)
        files.sort()
    except Exception:
        sys.exit(2)
    return files

def read_text(filepath):
    try:
        f = open(filepath,"r")
        texts = f.readlines()
        i = 0
        while i < len(texts):
            texts[i]= texts[i].strip("\n")
            i+=1
    except Exception:
        print("error")
    return texts

def EHLO(client_sock: socket.socket) -> None:
    client_sock.send(b"EHLO 127.0.0.1\r\n")

def check_status_code(client_sock: socket.socket, status_code: int) -> None:
    server_data = client_sock.recv(256)
    ls = server_data.decode().split()
    actual_status_code = int(ls[0])
    if actual_status_code != status_code:
        return False
    else:
        return True

def main():
    # TODO
    IP = 'localhost'
    PORT, send_path = parse_conf_path()
    files = directory_lis(send_path)
    dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dataSocket.settimeout(20)
    try:
        dataSocket.connect((IP,PORT))
    except TimeoutError:
        print("C: Cannot establish connection\r\n") 
    if (check_status_code(dataSocket,220)):
        EHLO(dataSocket)

    i = 0
    while i < len(files):
        text = read_text(files[i])
        j = 0
        while j < len(text):
            data = text[j]+"\r\n"
            dataSocket.send(data.encode())
            if (text[j]=="QUIT"):
                break
            j+=1
    dataSocket.close()

if __name__ == '__main__':
    main()