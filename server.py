import os
import socket
import sys

# Visit https://edstem.org/au/courses/8961/lessons/26522/slides/196175 to get
PERSONAL_ID = 'B03FFA'
PERSONAL_SECRET = '113619c855557bbe68464878e6aea7d3'

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
        print("S: "+respond_message,end="\r\n",flush=True)
        data_socket.send((respond_message+"\r\n").encode())
    else:
        respond_message = "250 127.0.0.1"
        print("S: "+respond_message,end="\r\n",flush=True)
        data_socket.send((respond_message+"\r\n").encode())
        #authenticity check
        respond_message = "250 AUTH CRAM-MD5"
        print("S: "+respond_message,end="\r\n",flush=True)
        data_socket.send((respond_message+"\r\n").encode())

def QUIT(data_socket):
    send_msg = "221 Service closing transmission channel"
    print("S: "+send_msg,end="\r\n",flush=True)
    data_socket.send((send_msg+"\r\n").encode())

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

def check_syntax(datasocket, info):
    '''
    param info - the entire message String from the client
    for the purpose of checking whether syntex is correct
    otherwise print and send 503 error 
    '''
    syntax_correct = True
    error_msg = "501 Syntax error in parameters or arguments"
    info_ls = info.split(" ")
    if info_ls[0] == "EHLO":
        if len(info_ls) != 2:
            syntax_correct = False
        else:
            port_number = info_ls[1].split(".")
            if len(port_number) != 4:
                syntax_correct = False
            for num in port_number:
                if int(num) < 0 or int(num)>255:
                    syntax_correct = False
    if not syntax_correct:
        print("S: "+error_msg,end="\r\n",flush=True)
        datasocket.send((error_msg+"\r\n").encode())
    return syntax_correct

def main():
    # TODO
    BUFLEN = 1024
    IP = 'localhost'
    PORT, path = parse_conf_path()
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((IP,PORT))
        s.listen()
        stage = 0
        conn, addr = s.accept()
        send_msg = "220 Service ready"
        print("S: "+send_msg,end="\r\n",flush=True)
        stage = 1
        conn.send((send_msg+"\r\n").encode())
        while True:
            recved = conn.recv(BUFLEN)
            info = recved.decode()
            if check_syntax(info):
                if not recved or info=="QUIT":
                    print("going to break")
                    break
                print("C: "+info.strip("\r\n"),end="\r\n",flush=True)
                if (info[0:4]=="EHLO" and stage==1):
                    EHLO(conn,info)
                    stage = 2
                elif (info[0:4]=="MAIL" and stage==3):
                    pass
                elif(info[0:4]=="QUIT"):
                    QUIT(conn)
        conn.close()
        s.close()

if __name__ == '__main__':
    main()
