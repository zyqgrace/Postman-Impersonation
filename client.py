import os
import socket
from socket import *
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
    return int(server_port),send_path

def read_text(send_path):
    files = []
    for file in os.listdir(send_path):
        files.append(file)
    files = files.sort()
    texts = []
    for f in files:
        f = open(send_path,'r')
        texts += f.readlines()
        f.close()
    return texts

def main():
    # TODO
    IP = "127.0.0.1"
    PORT, send_path = parse_conf_path()
    texts = read_text(send_path)
    dataSocket = socket(AF_INET, SOCK_STREAM)
    dataSocket.connect((IP,PORT))
    i = 0
    while i < len(texts):
        send_text = texts[i]
        if send_text == 'QUIT':
            break
        print("C: "+send_text)
        dataSocket.send(send_text.encode())
        i+=1
    dataSocket.close()