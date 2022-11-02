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
        respond_msg = "250 127.0.0.1"
        print("S: "+respond_msg,end="\r\n",flush=True)
        #authenticity check
        auth_msg = "250 AUTH CRAM-MD5"
        print("S: "+auth_msg,end="\r\n",flush=True)
        data_socket.send((respond_msg+"\r\n"+auth_msg+"\r\n").encode())

def QUIT(data_socket):
    send_msg = "221 Service closing transmission channel"
    print("S: "+send_msg,end="\r\n",flush=True)
    data_socket.send((send_msg+"\r\n").encode())

def check_stage(datasocket, info,stage):
    sequence = [["EHLO"],['AUTH',"MAIL"],["RCPT"],["DATA"]]
    for s in sequence[stage]:
        if info == s:
            return True
    if info == "QUIT":
        return True
    respond_msg = "503 Bad sequence of commands"
    print("S: "+respond_msg,end="\r\n",flush=True)
    datasocket.send((respond_msg+"\r\n").encode())
    return False

def check_email_format(info):
    '''
    correct example of info : <bob@bob.org>
    '''
    part1 = False
    part2 = False
    part3 = False
    if info[0] == "<":
        part1 = True
    i = 1
    subdomain = True
    while i < len(info):
        if subdomain and info[i]==".":
            return False
        elif not subdomain and info[i]==".":
            part2 = True
        if info[i]=="@":
            subdomain = False
        i+=1
    if info[-3]==">":
        part3 = True
    if part1 == True and part2 == True and part3 == True:
        return True
    return False

def check_syntax(datasocket, info):
    '''
    param info - the entire message String from the client
    for the purpose of checking whether syntex is correct
    otherwise print and send 503 error 
    '''
    syntax_correct = True
    error_msg = "501 Syntax error in parameters or arguments"
    info_ls = info.split(" ")
    if info_ls[0][0:4] == "EHLO":
        if len(info_ls) != 2:
            syntax_correct = False
        else:
            port_number = info_ls[1].split(".")
            if len(port_number) != 4:
                syntax_correct = False
            for num in port_number:
                if int(num) < 0 or int(num)>255:
                    syntax_correct = False
    elif info_ls[0][0:4]=="QUIT":
        if info_ls[0] != "QUIT\r\n":
            syntax_correct = False
    elif info_ls[0][0:4]=="MAIL":
        syntax_correct = False
        if len(info_ls) == 2:
            if info_ls[1][0:5] == "FROM:" and check_email_format(info_ls[1][5:]):
                syntax_correct = True
    elif info_ls[0][0:4]=="RCPT":
        syntax_correct = False
        if len(info_ls) == 2:
            if info_ls[1][0:3] == "TO:" and check_email_format(info_ls[1][3:]):
                syntax_correct = True
    elif info_ls[0] == "AUTH":
        if info_ls[1] != "CRAM-MD5\r\n":
            syntax_correct = False
    if not syntax_correct:
        print("S: "+error_msg,end="\r\n",flush=True)
        datasocket.send((error_msg+"\r\n").encode())
    return syntax_correct

def AUTH(datasocket,info):
    pass

def MAIL(datasocket,info):
    respond_msg = "250 Requested mail action okay completed"
    print("S: "+respond_msg,end="\r\n",flush=True)
    datasocket.send((respond_msg+"\r\n").encode())

def RCPT(datasocket,info):
    respond_msg = "250 Requested mail action okay completed"
    print("S: "+respond_msg,end="\r\n",flush=True)
    datasocket.send((respond_msg+"\r\n").encode())

def main():
    # TODO
    BUFLEN = 1024
    IP = 'localhost'
    PORT, path = parse_conf_path()
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((IP,PORT))
        s.listen()
        conn, addr = s.accept()
        send_msg = "220 Service ready"
        print("S: "+send_msg,end="\r\n",flush=True)
        stage = 0
        conn.send((send_msg+"\r\n").encode())
        while True:
            recved = conn.recv(BUFLEN)
            info = recved.decode()
            if not recved:
                err_msg = "Connection lost"
                print("S: "+err_msg,end="\r\n",flush=True)
                break
            print("C: "+info.strip("\r\n"),end="\r\n",flush=True)
            if check_stage(conn,info[0:4],stage):
                if check_syntax(conn, info):
                    if info[0:4]=="EHLO":
                        EHLO(conn,info)
                        stage = 1
                    elif info[0:4]=="AUTH":
                        stage = 2
                    elif info[0:4]=="MAIL":
                        MAIL(conn,info)
                        stage = 2
                    elif info[0:4]=="RCPT":
                        RCPT(conn,info)
                        stage = 3
                    elif (info[0:4]=="QUIT"):
                        QUIT(conn)
                        break
        conn.close()
        s.close()

if __name__ == '__main__':
    main()
