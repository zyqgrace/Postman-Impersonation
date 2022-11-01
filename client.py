import os
import socket
import sys
from dataclasses import dataclass

# Visit https://edstem.org/au/courses/8961/lessons/26522/slides/196175 to get
PERSONAL_ID = 'B03FFA'
PERSONAL_SECRET = '113619c855557bbe68464878e6aea7d3'

class Email:
    def __init__(self,From,to,date,subject,body):
        self.From = From
        self.to = to
        self.date = date
        self.subject = subject
        self.body = body

def parse_conf_path():
    server_port = None
    send_path = None
    if len(sys.argv)<= 1:
        sys.exit(1)
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
    if(not os.path.isdir(send_path)):
        sys.exit(2)
    try:
        for file in os.listdir(send_path):
            files.append(send_path+"/"+file)
        files.sort()
    except Exception:
        sys.exit(2)
    return files

def read_text(filepath):
    """
    This aims to read the text from absolute filepath parse
    and return information as an Email instance
    """
    try:
        f = open(filepath,"r")
        texts = f.readlines()
        From = None
        To = None
        Date = None
        Subject = None
        Body = []
        if texts[0][0:4] == 'From':
            From = texts[0][6:-1]
        elif texts[1][0:2] == "To":
            To = texts[1][4:-1]
        elif texts[2][0:4] == "Date":
            Date = texts[2][0:-1]
        elif texts[3][0:7] == "Subject":
            Subject = texts[3][0:-1]
        i = 4
        while i < len(texts):
            Body.append(texts[i].strip("\n"))
            i+=1
        if From == None or To == None or Date == None or Subject == None:
            print("C: "+os.path.abspath(filepath)+": Bad formation",end="\r\n",flush=True)
            sys.exit(0)
    except Exception:
        print("error")
    return Email(From, To, Date, Subject, Body)


def send_email_via_server(client_socket, email):
    with client_socket:
        if check_status_code(client_socket, 220):
            EHLO(client_socket)
        if check_status_code(client_socket,250):
            mail_from = "MAIL FROM:"+email.From+"\r\n"
            print("C: "+"MAIL FROM:"+email.From,end='\r\n',flush=True)
            client_socket.send(mail_from.encode())
        if check_status_code(client_socket,250):
            RCPT(client_socket,email.to)
        print("C: DATA",end="\r\n",flush = True)
        client_socket.send(b"DATA\r\n")
        if check_status_code(client_socket, 354):
            date = email.date+ "\r\n"
            print("C: "+email.date,end="\r\n",flush=True)
            client_socket.send(date.encode())
        if check_status_code(client_socket, 354):
            subject = email.subject + "\r\n"
            print("C: "+ email.subject,end="\r\n",flush=True)
            client_socket.send(subject.encode())
        if check_status_code(client_socket, 354):
            for text in email.body:
                print("C: "+text,end="\r\n",flush=True)
                text = text+"\r\n"
                client_socket.send(text.encode())
                if check_status_code(client_socket, 354):
                    pass
            print("C: .",end="\r\n",flush=True)
            client_socket.send(b".\r\n")
        if check_status_code(client_socket, 250):
            print("C: QUIT",end="\r\n",flush=True)
            client_socket.send(b"QUIT\r\n")
        if check_status_code(client_socket, 221):
            pass

def EHLO(client_sock: socket.socket) -> None:
    print("C: EHLO 127.0.0.1", end = "\r\n",flush=True)
    client_sock.send(b"EHLO 127.0.0.1\r\n")

def RCPT(client_socket,recipients):
    recipients = recipients.split(",")
    for r in recipients:
        send_to = "RCPT TO:" + r + "\r\n"
        print("C: "+"RCPT TO:" + r,end='\r\n',flush=True)
        client_socket.send(send_to.encode())
        check_status_code(client_socket,250)

def check_status_code(client_sock: socket.socket, status_code: int) -> None:
    server_data = client_sock.recv(256)
    data = server_data.decode().strip("\r\n")
    print("S: "+data,end="\r\n",flush=True)
    data_ls = data.split()
    actual_status_code = int(data_ls[0])
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
    for filepath in files:
        try:
            dataSocket.connect((IP,PORT))
        except ConnectionRefusedError:
            print("C: Cannot establish connection",end="\r\n",flush=True) 
            sys.exit(3)
        email = read_text(filepath)
        send_email_via_server(dataSocket,email)
        dataSocket.close()

if __name__ == '__main__':
    main()