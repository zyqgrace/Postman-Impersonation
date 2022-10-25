import os
import socket
from socket import *
import sys

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
            elif info[0:10] == "inbox_path":
                send_path = info[11:]
    except FileNotFoundError:
        sys.exit(1)
    if server_port.isnumeric() == False:
        sys.exit(2)
    elif int(server_port) <= 1024:
        sys.exit(2)
    elif send_path == None:
        sys.exit(2)
    return int(server_port),send_path

def main():
    # TODO
    IP = "127.0.0.1"
    PORT, path = parse_conf_path()
    print(PORT)
    print(path)
    listenSocket = socket(AF_INET,SOCK_STREAM)
    listenSocket.bind((IP,PORT))
    listenSocket.listen(5)
    dataSocket, addr = listenSocket.accept()


if __name__ == '__main__':
    main()
