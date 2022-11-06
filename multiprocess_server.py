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

def recognize_command(info):
    valid = ["EHLO","MAIL","RCPT","DATA","RSET",
            "NOOP","AUTH","QUIT"]
    return info[0:4] in valid

def check_stage(info,stage):
    sequence = [["EHLO"],['AUTH',"MAIL"],["RCPT"],["RCPT","DATA"]]
    for s in sequence[stage]:
        if info == s:
            return True
    if info == "QUIT" or info =="RSET" or info == "NOOP":
        return True
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

def send_code(datasocket,num):
    '''
    return list of send code
    '''
    code = {
        220:"220 Service ready",
        250:"250 Requested mail action okay completed",
        221:"221 Service closing transmission channel",
        501:"501 Syntax error in parameters or arguments",
        500: "500 Syntax error,command unrecognized",
        503:"503 Bad sequence of commands",
        235:"235 Authentication successful",
        504: "504 Unrecognized authentication type",
        535: "535 Authentication credentials invalid",
        354:"354 Start mail input end <CRLF>.<CRLF>"
    }
    datasocket.send((code[num]+"\r\n").encode())
    return ["S: "+code[num]]

def EHLO(data_socket):
    '''
    message - entire recved from client
    example EHLO 127.0.0.1
    interpret the message whether it is valid and respond the EHLO command.
    '''
    return_msg = []
    respond_msg = "250 127.0.0.1"
    #authenticity check
    auth_msg = "250 AUTH CRAM-MD5"
    data_socket.send((respond_msg+"\r\n"+auth_msg+"\r\n").encode())
    return_msg.append("S: "+respond_msg)
    return_msg.append("S: "+auth_msg)
    return return_msg

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
    return_msg = []
    error_msg = "501 Syntax error in parameters or arguments"
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
    elif info_ls[0] == "AUTH":
        if info_ls[1] != "CRAM-MD5\r\n":
            return_msg = send_code(datasocket,504)
            return False,return_msg
    elif info_ls[0][0:4]=="RSET":
        if len(info_ls)!=1:
            syntax_correct = False
    elif info_ls[0][0:4]=="NOOP":
        if len(info_ls)!=1:
            syntax_correct = False
    if not syntax_correct:
        return_msg.append("S: "+error_msg)
        datasocket.send((error_msg+"\r\n").encode())
    return syntax_correct,return_msg

def AUTH(datasocket):
    return_msg = []
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
    return_msg.append("S: "+result)
    datasocket.send((result+"\r\n").encode())
    return False,return_msg

def DATA(datasocket,info):
    '''
    return text as a list of all content from Date
    '''
    return_msg = []
    return_msg+=send_code(datasocket,354)
    text = []
    while True:
        recved = datasocket.recv(1024)
        info = recved.decode()
        if not recved:
            err_msg = "Connection lost"
            return_msg.append("S: "+err_msg)
            break
        return_msg.append("C: "+info.strip("\r\n"))
        if info == ".\r\n":
            break
        text.append(info)
        return_msg+=send_code(datasocket,354)
    return_msg+=send_code(datasocket,250)
    return text,return_msg

def write_file(path, sender, receivers, body,prefix):
    '''
    read file to given path
    '''
    filename = None
    cur_time = body[0].strip("\r\n")
    try:
        date_format = datetime.datetime.strptime(cur_time, 
                    'Date: %a, %d %b %Y %H:%M:%S %z')
        filename = prefix+str(int(datetime.datetime.timestamp(date_format)))+".txt"
    except ValueError:
        filename = prefix+"unknown.txt"
    try:
        f = open(path+"/"+filename,"a")
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
    except Exception:
        pass

def main():
    number = 0
    BUFLEN = 1024
    IP = 'localhost'
    PORT, path = parse_conf_path()
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((IP,PORT))
        s.listen()
        s.settimeout(20)
        while True:
            try:
                conn, addr = s.accept()
                number+=1
            except TimeoutError:
                break
            pid = os.fork()
            if pid == 0:
                prefix = f'[{os.getpid()}][{number:02d}]'
                stage = 0
                stdout = []
                stdout+=send_code(conn,220)
                MAIL_from = None
                RCPT_to = []
                text = ''
                while True:
                    recved = conn.recv(BUFLEN)
                    info = recved.decode()
                    if not recved:
                        err_msg = "Connection lost"
                        stdout.append("S: "+err_msg)
                        break
                    stdout.append("C: "+info.strip("\r\n"))
                    if recognize_command(info)==False:
                        stdout+=send_code(conn,500)
                        continue
                    if check_stage(info[0:4],stage) == False:
                        stdout+=send_code(conn,503)
                        continue
                    syntax_correct, text = check_syntax(conn, info)
                    stdout+=text
                    if syntax_correct:
                        if info[0:4]=="EHLO":
                            stdout+=EHLO(conn)
                            stage = 1
                        elif info[0:4]=="AUTH":
                            next, text = AUTH(conn)
                            stdout+=text
                            if next:
                                stage = 2
                        elif info[0:4]=="MAIL":
                            MAIL_from = info.split(" ")[1][5:]
                            stdout+=send_code(conn,250)
                            stage = 2
                        elif info[0:4]=="RCPT":
                            RCPT_to.append(info[8:-2])
                            stdout+=send_code(conn,250)
                            stage = 3
                        elif info[0:4]=="QUIT":
                            stdout+=send_code(conn,221)
                            break
                        elif info[0:4]=="RSET":
                            stdout+=send_code(conn,250)
                            if stage != 0:
                                stage = 1
                        elif info[0:4]=="DATA":
                            text,return_msg= DATA(conn,info)
                            stdout+=return_msg
                            write_file(path,MAIL_from,RCPT_to,text,prefix)
                        elif info[0:4]=="NOOP":
                            stdout+=send_code(conn,250)
                for output in stdout:
                    print(prefix+output,end="\r\n",flush=True)
                os._exit(os.EX_OK)
        conn.close()
        s.close()

if __name__ == '__main__':
    main()