import os
import socket
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

def EHLO(data_socket,message):
    '''
    message - entire recved from client
    example EHLO 127.0.0.1
    interpret the message whether it is valid and respond the EHLO command.
    '''
    command = message.split(" ")
    if (len(command)==1):
        respond_message = "501 Syntax error in parameters or arguments"
    if (len(command) == 2):
        respond_message = "250 "+command[1]
    print("S: "+respond_message,end="\r\n",flush=True)
    data_socket.send(respond_message.encode())
    #authenticity check
    respond_message = "250 AUTH CRAM-MD5"
    print("S: "+respond_message,end="\r\n",flush=True)
    data_socket.send(respond_message.encode())


def detect_message(data_socket, message):
    info = message.decode()
    info_ls = info.split()
    if info_ls[0] == "QUIT":
        send = "221 Service closing transmission channel"
    elif info_ls[0] == "EHLO":
        send = "250 "+info_ls[1]
    print("S: "+send)
    data = send+"\r\n"
    data_socket.send(data.encode())

def main():
    # TODO
    BUFLEN = 1024
    IP = 'localhost'
    PORT, path = parse_conf_path()
    listenSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listenSocket.bind((IP,PORT))
    listenSocket.listen(5)
    stage = 0
    dataSocket, addr = listenSocket.accept()
    print("S: 220 Service ready",end="\r\n",flush=True)
    stage = 1
    with dataSocket:
        while True:
            recved = dataSocket.recv(BUFLEN)
            if not recved:
                break
            info = recved.decode()
            print("C: "+info.strip("\n"),end="\r\n",flush=True)
            if (info[0:4]=="EHLO" and stage==1):
                EHLO(dataSocket,info)
                stage = 2
            else:
                detect_message(dataSocket,recved)
    dataSocket.close()
    listenSocket.close()

if __name__ == '__main__':
    main()
