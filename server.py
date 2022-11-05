import os
import socket
import sys
import base64
import secrets
import string
import hmac
import datetime

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
    if server_port == None or send_path == None:
        sys.exit(2)
    elif int(server_port) <= 1024:
        sys.exit(2)
    send_path = os.path.expanduser(send_path)
    return int(server_port),send_path

def EHLO(data_socket):
    '''
    message - entire recved from client
    example EHLO 127.0.0.1
    interpret the message whether it is valid and respond the EHLO command.
    '''
    respond_msg = "250 127.0.0.1"
    print("S: "+respond_msg,end="\r\n",flush=True)
    #authenticity check
    auth_msg = "250 AUTH CRAM-MD5"
    print("S: "+auth_msg,end="\r\n",flush=True)
    data_socket.send((respond_msg+"\r\n"+auth_msg+"\r\n").encode())

def check_stage(datasocket, info,stage):
    sequence = [["EHLO"],['AUTH',"MAIL"],["RCPT"],["RCPT","DATA"]]
    for s in sequence[stage]:
        if info == s:
            return True
    if info == "QUIT" or info =="RSET" or info == "NOOP":
        return True
    send_code(datasocket,503)
    return False

def check_ip_addr(ip):
    ip = ip.split(".")
    if len(ip) != 4:
        return False
    for num in ip:
        if not num.isnumeric():
            return False
        if int(num) > 255 or int(num) < 0:
            return False
    return True

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
    info_ls = info.split(" ")
    if info_ls[0][0:4] == "EHLO":
        if len(info_ls) != 2:
            syntax_correct = False
        else:
            if check_ip_addr(info_ls[1][:-2]) == False:
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
    elif info_ls[0][0:4] == "AUTH":
        if len(info_ls) != 2:
            syntax_correct = False
        else:
            if info_ls[1] != "CRAM-MD5\r\n":
                send_code(datasocket,504)
                return False
    elif info_ls[0][0:4]=="RSET":
        if len(info_ls)!=1:
            syntax_correct = False
    elif info_ls[0][0:4]=="NOOP":
        if len(info_ls)!=1:
            syntax_correct = False
    if not syntax_correct:
        send_code(datasocket,501)
    return syntax_correct

def AUTH(datasocket):
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(50))
    challenge = base64.b64encode(password.encode())
    send_msg = b"334 "+challenge+b"\r\n"
    datasocket.send(send_msg)
    anwser = datasocket.recv(256)
    base64_answer = base64.b64decode(anwser)
    print(base64_answer)
    server_hmac = hmac.new(PERSONAL_SECRET.encode(),password.encode("ascii"),digestmod="md5")
    server_answer = PERSONAL_ID+" "+server_hmac.hexdigest()
    if server_answer == base64_answer:
        send_code(datasocket,235)
        return True
    else:
        send_code(datasocket,535)
        return False

def send_code(datasocket,num):
    code = {
        220:"220 Service ready",
        250:"250 Requested mail action okay completed",
        221:"221 Service closing transmission channel",
        501:"501 Syntax error in parameters or arguments",
        503:"503 Bad sequence of commands",
        235:"235 Authentication successful",
        504: "504 Unrecognized authentication type",
        535: "535 Authentication credentials invalid",
        354:"354 Start mail input end <CRLF>.<CRLF>"
    }
    print("S: "+code[num],end="\r\n",flush=True)
    datasocket.send((code[num]+"\r\n").encode())

def DATA(datasocket,info):
    '''
    return text as a list of all content from Date
    '''
    send_code(datasocket,354)
    text = []
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
        text.append(info)
        send_code(datasocket,354)
    send_code(datasocket,250)
    return text

def write_file(path, sender, receivers, body,auth_pass):
    '''
    write the email to given path
    '''
    filename = None
    cur_time = body[0].strip("\r\n")
    try:
        date_format = datetime.datetime.strptime(cur_time, 
                    'Date: %a, %d %b %Y %H:%M:%S %z')
        filename = str(int(datetime.datetime.timestamp(date_format)))+".txt"
    except Exception:
        filename = "unknown.txt"
    if auth_pass:
        filename = "auth."+filename
    try:
        f = open(path+"/"+filename,"w")
        f.write("From: "+sender.replace("\r\n","\n"))
        receiver_str = ""
        for i in range(len(receivers)-1):
            receiver_str+=(receivers[i].strip("\r\n")+",")
        receiver_str+=receivers[-1].strip("\r\n")
        f.write("To: "+receiver_str+"\n")
        for text in body:
            text = text.replace("\r\n","\n")
            f.write(text)
        f.close()
    except IOError:
        sys.exit(2)

def main():
    BUFLEN = 1024
    IP = 'localhost'
    PORT, path = parse_conf_path()
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((IP,PORT))
            s.listen()
        except socket.error:
            sys.exit(2)
        conn, addr = s.accept()
        send_code(conn,220)
        stage = 0
        MAIL_from = None
        auth_pass = False
        RCPT_to = []
        text = ''
        while True:
            recved = conn.recv(BUFLEN)
            info = recved.decode()
            if not recved:
                print("S: Connection lost",end="\r\n",flush=True)
                break
            print("C: "+info.strip("\r\n"),end="\r\n",flush=True)
            if check_stage(conn,info[0:4],stage):
                if check_syntax(conn, info):
                    if info[0:4]=="EHLO":
                        EHLO(conn)
                        stage = 1
                    elif info[0:4]=="AUTH":
                        if AUTH(conn):
                            stage = 2
                            auth_pass = True
                    elif info[0:4]=="MAIL":
                        MAIL_from = info.split(" ")[1][5:]
                        send_code(conn,250)
                        stage = 2
                    elif info[0:4]=="RCPT":
                        RCPT_to.append(info[8:-2])
                        send_code(conn,250)
                        stage = 3
                    elif info[0:4]=="QUIT":
                        send_code(conn,221)
                        break
                    elif info[0:4]=="RSET":
                        send_code(conn,250)
                        if stage != 0:
                            stage = 1
                    elif info[0:4]=="DATA":
                        text = DATA(conn,info)
                        write_file(path, MAIL_from, RCPT_to, text, auth_pass)
                    elif info[0:4]=="NOOP":
                        send_code(conn,250)
        conn.close()
        s.close()

if __name__ == '__main__':
    main()
