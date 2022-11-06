import os
import socket
import sys
import datetime

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
                spy_path = info[9:]
    except FileNotFoundError:
        sys.exit(1)
    if server_port == None or client_port == None or spy_path ==None:
        sys.exit(2)
    elif not server_port.isnumeric() or not client_port.isnumeric():
        sys.exit(2)
    elif int(server_port) <= 1024 or int(client_port) <= 1024:
        sys.exit(2)
    elif  int(server_port) == int(client_port):
        sys.exit(2)
    try:
        spy_path = os.path.expanduser(spy_path)
    except Exception:
        sys.exit(2)
    return int(server_port),int(client_port),spy_path

def write_file(path,sender,receivers,body):
    filename = None
    cur_time = body[0].strip("\r\n")
    date_format = datetime.datetime.strptime(cur_time, 
                  'Date: %a, %d %b %Y %H:%M:%S %z')
    filename = str(int(datetime.datetime.timestamp(date_format)))+".txt"
    try:
        f = open(path+"/"+filename,"a")
        f.write("From: "+sender + "\n")
        receiver_str = ""
        for i in range(len(receivers)-1):
            receiver_str+=(receivers[i].strip("\r\n")+",")
        receiver_str+=receivers[-1].strip("\r\n")
        f.write("To: "+receiver_str+"\n")
        for text in body:
            text = text.replace("\r\n","\n")
            f.write(text)
        f.close()
    except Exception:
        sys.exit(1)

def main():
    # TODO
    IP = "localhost"
    server_port, client_port, path = parse_conf_path()
    MAIl_from = None
    RCPT_to = []
    text = []
    record=False
    quit = False
    try:
        AS = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        AS.connect((IP,server_port))
    except socket.error:
        print("AS: Cannot establish connection",end="\r\n",flush=True)
        sys.exit(3)

    AC = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    AC.bind((IP,client_port))
    AC.listen()
    conn, addr = AC.accept()

    while True:
        recved = AS.recv(1024)
        info = (recved.decode()).split("\r\n")
        if not recved:
            print("AS: Connection lost",end="\r\n",flush=True)
            sys.exit(3)
        for i in info[:-1]:
            print("S: "+i,end="\r\n",flush=True)
        for i in info[:-1]:
            print("AC: "+i,end="\r\n",flush=True)
        conn.send(recved)
        if quit and info[0][0:3]=="221":
            sys.exit(0)

        recved = conn.recv(1024)
        info = recved.decode()
        if not recved:
            print("AC: Connection lost",end="\r\n",flush=True)
            break
        print("C: "+info.strip("\r\n"),end="\r\n",flush=True)
        print("AS: "+info.strip("\r\n"),end="\r\n",flush=True)
        if info == ".\r\n":
            record = False
            write_file(path,MAIL_from,RCPT_to,text)
        if record:
            text.append(info)
        if info[0:4]=="MAIL":
            MAIL_from = info[10:-2]
        if info[0:4]=="RCPT":
            RCPT_to.append(info[8:-2])
        if info[0:4]=="DATA":
            record = True
        AS.send(recved)
        if info[0:4]=="QUIT":
            quit = True
    AC.close()
    conn.close()
if __name__ == '__main__':
    main()
