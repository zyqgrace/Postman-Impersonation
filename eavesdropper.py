import os
import socket
import sys

def parse_conf_path():
    server_port = None
    client_port = None
    spy_path = None
    if len(sys.argv)<= 1:
        sys.exit(1)
    try:
        conf_path = open(sys.argv[1],'r')
        configuration = conf_path.readlines()
        for info in configuration:
            info = info.strip("\r\n")
            if info[0:11] == "server_port":
                server_port = info[12:]
            elif info[0:11] == "client_port":
                client_port = info[12:]
            elif info[0:8] == "spy_path":
                send_path = info[9:]
    except FileNotFoundError:
        sys.exit(1)
    if server_port == None or client_port == None:
        sys.exit(2)
    elif not server_port.isnumeric() or not client_port.isnumeric():
        sys.exit(2)
    elif int(server_port) <= 1024 or int(client_port) <= 1024:
        sys.exit(2)
    elif spy_path == None:
        sys.exit(2)
    spy_path = os.path.expanduser(send_path)
    return int(server_port),int(client_port),spy_path

def main():
    # TODO
    IP = "localhost"
    server_port, client_port, path = parse_conf_path()
    
    MAIl_FROM = None
    RCPT_to = []
    text = ''
    filename = None
    try:
        pretent_client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        pretent_client.connect((IP,server_port))
    except Exception:
        print("AS: Cannot establish connection",end="\r\n",flush=True)
        sys.exit(3)
    try:
        pretent_server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        pretent_server.bind((IP,client_port))
        pretent_server.listen()
        conn, addr = pretent_server.accept()
    except Exception:
        print("AC: Connection lost",end="\r\n",flush=True)
        sys.exit(3)

    while True:
        recved = pretent_client.recv(1024)
        info = recved.decode()
        if not recved:
            print("AS: Connection lost",end="\r\n",flush=True)
            sys.exit(3)
        print("S: "+info.strip("\r\n"),end="\r\n",flush=True)
        print("AC: "+info.strip("\r\n"),end="\r\n",flush=True)
        pretent_server.send(recved)

        recved = pretent_server.recv(1024)
        info = recved.decode()
        if not recved:
            print("AC: Connection lost",end="\r\n",flush=True)
            sys.exit(3)
        print("C: "+info.strip("\r\n"),end="\r\n",flush=True)
        print("AS: "+info.strip("\r\n"),end="\r\n",flush=True)
        pretent_client.send(recved)
        
if __name__ == '__main__':
    main()
