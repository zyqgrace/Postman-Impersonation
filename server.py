import os
import socket
import sys
import base64
import secrets
import string
import hmac

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
    sequence = [["EHLO"],['AUTH',"MAIL"],["RCPT"],["RCPT","DATA"]]
    for s in sequence[stage]:
        if info == s:
            return True
    if info == "QUIT" or info =="RSET" or info == "NOOP":
        return True
    respond_msg = "503 Bad sequence of commands"
    print("S: "+respond_msg,end="\r\n",flush=True)
    datasocket.send((respond_msg+"\r\n").encode())
    return False

def isletdig(char):
    return char.isalpha() or char.isnumeric()
    
def check_email_format(info):
    '''
    correct example of info : <bob@bob.org>
    '''
    Format = False
    if info[0] != '<' or info[-3:]!=">\r\n":
        return False
    mailbox = info[1:-3].split("@")
    if len(mailbox)==1:
        return False
    i = 1
    dot = False
    domain = 0
    atom_start = True
    while i < len(info[1:-3]):
        if atom_start:
            if not isletdig(info[i]):
                return False
        else:
            if info[i]==".":
                i+=1
                atom_start = True
                if domain ==1:
                    dot = True
                continue
            if domain == 0:
                if info[i]=="@":
                    atom_start = True
                    domain+=1
                    i+=1
                    continue
                if not(isletdig(info[i]) or info[i]=="-"):
                    return False
            else:
                if info[i]=="-":
                    if i == len(info[1:-3])-1:
                        return False
                    i+=1
                    if not(isletdig(info[i])):
                        return False
        atom_start = False
        i+=1
    if dot != True:
        return False
    return True

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
            if info_ls[1][0:5] == "FROM:" and len(info_ls[1])>7:
                syntax_correct = check_email_format(info_ls[1][5:])
    elif info_ls[0][0:4]=="RCPT":
        syntax_correct = False
        if len(info_ls) == 2:
            if info_ls[1][0:3] == "TO:" and len(info_ls[1])>5:
                syntax_correct = check_email_format(info_ls[1][3:])
    elif info_ls[0] == "AUTH":
        if info_ls[1] != "CRAM-MD5\r\n":
            error_msg = "504 Unrecognized authentication type"
            print("S: "+error_msg,end="\r\n",flush=True)
            datasocket.send((error_msg+"\r\n").encode())
            return False
    elif info_ls[0][0:4]=="RSET":
        if len(info_ls)!=1:
            syntax_correct = False
    elif info_ls[0][0:4]=="NOOP":
        if len(info_ls)!=1:
            syntax_correct = False
    if not syntax_correct:
        print("S: "+error_msg,end="\r\n",flush=True)
        datasocket.send((error_msg+"\r\n").encode())
    return syntax_correct

def AUTH(datasocket,info):
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(50))
    challenge = base64.b64encode(password.encode())
    send_msg = b"334 "+challenge+b"\r\n"
    datasocket.send(send_msg)
    anwser = datasocket.recv(256)
    base64_answer = base64.b64decode(anwser)
    client_digest = base64_answer.decode().split(" ")[1]
    server_hmac = hmac.new(PERSONAL_SECRET.encode(),password.encode(),digestmod="md5")
    if hmac.compare_digest(server_hmac.hexdigest(),client_digest):
        result = "235 Authentication successful"
    else:
        result = "535 Authentication credentials invalid"
    print("S: "+result,end="\r\n",flush=True)
    datasocket.send((result+"\r\n").encode())
    return False

def MAIL(datasocket,info):
    respond_msg = "250 Requested mail action okay completed"
    print("S: "+respond_msg,end="\r\n",flush=True)
    datasocket.send((respond_msg+"\r\n").encode())

def RCPT(datasocket,info):
    respond_msg = "250 Requested mail action okay completed"
    print("S: "+respond_msg,end="\r\n",flush=True)
    datasocket.send((respond_msg+"\r\n").encode())

def RSET(datasocket,info):
    respond_msg = "250 Requested mail action okay completed"
    print("S: "+respond_msg,end="\r\n",flush=True)
    datasocket.send((respond_msg+"\r\n").encode())

def NOOP(datasocket,info):
    respond_msg = "250 Requested mail action okay completed"
    print("S: "+respond_msg,end="\r\n",flush=True)
    datasocket.send((respond_msg+"\r\n").encode())

def DATA(datasocket,info):
    respond_msg = "354 Start mail input end <CRLF>.<CRLF>"
    print("S: "+respond_msg,end="\r\n",flush=True)
    datasocket.send((respond_msg+"\r\n").encode())
    text = ""
    while True:
        recved = datasocket.recv(1024)
        info = recved.decode()
        if not recved:
            err_msg = "Connection lost"
            print("S: "+err_msg,end="\r\n",flush=True)
            break
        print("C: "+info.strip("\r\n"),end="\r\n",flush=True)
        if info == ".\r\n":
            break
        text+=info
        respond_msg = "354 Start mail input end <CRLF>.<CRLF>"
        print("S: "+respond_msg,end="\r\n",flush=True)
        datasocket.send((respond_msg+"\r\n").encode())
    respond_msg = "250 Requested mail action okay completed"
    print("S: "+respond_msg,end="\r\n",flush=True)
    datasocket.send((respond_msg+"\r\n").encode())
    return text

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
                        if AUTH(conn,info):
                            stage = 2
                    elif info[0:4]=="MAIL":
                        MAIL(conn,info)
                        stage = 2
                    elif info[0:4]=="RCPT":
                        RCPT(conn,info)
                        stage = 3
                    elif info[0:4]=="QUIT":
                        QUIT(conn)
                        break
                    elif info[0:4]=="RSET":
                        RSET(conn,info)
                        if stage != 0:
                            stage = 1
                    elif info[0:4]=="DATA":
                        DATA(conn,info)
                    elif info[0:4]=="NOOP":
                        NOOP(conn,info)
        conn.close()
        s.close()

if __name__ == '__main__':
    main()
