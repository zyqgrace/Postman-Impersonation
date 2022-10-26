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

def convert_text_to_email(texts):
    """
    This aims to parse text_ls in email form
    """
    From = None
    To = None
    Date = None
    Subject = None
    Body = []
    for text in texts:
        if text[0:4]=='From':
            From = text[6:]
        elif text[0:2] == "To":
            To = text[4:]
        elif text[0:4] == "Date":
            Date = text
        elif text[0:7] == "Subject":
            Subject = text
        else:
            Body.append(text)
    return Email(From, To, Date, Subject, Body)


def send_email_via_server(client_socket, text):
    with client_socket:
        if check_status_code(client_socket, 220):
            EHLO(client_socket)
        email = convert_text_to_email(text)
        if check_status_code(client_socket,250):
            mail_from = "MAIL FROM:"+email.From+"\r\n"
            client_socket.send(mail_from.encode())
        if check_status_code(client_socket,250):
            send_to = "RCPT TO:" + email.to + "\r\n"
            client_socket.send(send_to.encode())
        if check_status_code(client_socket,250):
            client_socket.send(b"DATA\r\n")
        if check_status_code(client_socket, 354):
            date = email.date+ "\r\n"
            client_socket.send(date.encode())
        if check_status_code(client_socket, 354):
            subject = email.subject + "\r\n"
            client_socket.send(subject.encode())
        if check_status_code(client_socket, 354):
            for text in email.body:
                text = text+"\r\n"
                client_socket.send(text.encode())

        
def EHLO(client_sock: socket.socket) -> None:
    print("EHLO 127.0.0.1\r\n",flush=True)
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
        print("S: 220 Service ready\r\n",flush=True)
    except TimeoutError:
        print("C: Cannot establish connection\r\n") 

    i = 0
    while i < len(files):
        text = read_text(files[i])
        send_email_via_server(dataSocket,text)
        i+=1
    dataSocket.close()

if __name__ == '__main__':
    main()