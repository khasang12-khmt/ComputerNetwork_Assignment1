import threading, time
import socket, select
import json
from tkinter import *
from tkinter import font
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, askdirectory
import sys,json
from utils.protocol import Encode
import os
FORMAT = "utf-8"

# Your External IPv4
# EXTERNAL_IP_SERVER = '192.168.1.6'
EXTERNAL_IP_SERVER = "192.168.227.215" 

# This is The Peer Main Class act as A routing
# It will contain Server side and Client Side
# This peer will listen request sent from other Peer
START_CHECKING = False

class Peer_Central():
    
    def __init__(self):
        self.HOST = EXTERNAL_IP_SERVER
        self.PORT_TCP = 3000
        self.PORT_UDP = 3004
        self.central_client_socket = None
        self.userName = None
        self.password = None
        self.ip_addr = None
        self.port = None
        self.CONDITION = True
        self.startTime = 0
        self.endTime = 0
        self.running = True
        self.friendStatus = [] # Manage User Status
        self.HandleConnection = None # handle Connection
        self.Encoder = None
    
    def run(self):
        # Create central socket - TCP port
        self.central_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.central_client_socket.connect((self.HOST, self.PORT_TCP))
        except:
            print('Unable connection to central server unit')
        
        # Maintain online
        threading.Thread(target=self.checkConn).start()
    
    def checkConn(self):
        self.checkConn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        while self.running:
            if(START_CHECKING):
                self.endTime = time.time()
                elapsedTime = int(self.endTime - self.startTime)
                # send to server after 3 secs
                if (elapsedTime % 3) == 0:
                    data = str(self.userName + "," + "Hello")
                    # send attendance msg
                    self.checkConn.sendto(data.encode(), (self.HOST, int(self.PORT_UDP)))
                    # recv online users
                    
                    result = self.checkConn.recv(4096).decode()
                    newList = eval(result)
                    # print if updated
                    newFriendList = [x for x in newList if x!=self.userName]
                    if self.friendStatus != newFriendList:
                        self.friendStatus = newFriendList
                        printOnlineUsers(newFriendList)
                
            time.sleep(0.1)
    
    def registerClient(self, userName, password):       # có UI rồi
        self.central_client_socket.send("register".encode())
        
        self.userName = userName
        self.password = password
        
        data = str(self.userName + "," + self.password)
        
        self.central_client_socket.send(data.encode())
        print(data)
        processStatus = self.central_client_socket.recv(1024).decode()
        # server-side validation
        print(processStatus)
        if (processStatus!="Account created successfully - 1"):
            messagebox.showerror(title="Lỗi đăng kí",message="Username đã được sử dụng hoặc lỗi server. Hãy thử lại.")
        else:
            messagebox.showinfo(title="Đăng kí thành công",message="Vui lòng tiếp tục đăng nhập để được vào dịch vụ !!")
                
    def searchClient(self, userName):
        self.central_client_socket.send("search".encode())
        self.central_client_socket.send(userName.encode())
        
        # search trap - catch only valid data
        data = ""
        while True:
            res = self.central_client_socket.recv(1024).decode()
            if res.count(",") != 0:
                data = res.split(",")
                break
        peer_ip,peer_port = data
        
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((peer_ip, 80))
        # Send Request Chat
        conn.send(self.userName.encode(FORMAT))
        str = conn.recv(1024).decode(FORMAT)
        conn.send(self.Encoder.requestChat())

        # Wait Until Receive
        msg = conn.recv(1024).decode(FORMAT)
        msg = json.loads(msg)
        if(msg['code']==1):
            self.HandleConnection.createClientThread(conn,self.ip_addr,self.port,userName)
        else:
            print("Peer Decline Chat")
        self.HandleConnection.join()
                    
    def loginClient(self, userName, password):          # có UI rồi
        hostname = socket.gethostname()
        ip_addr = socket.gethostbyname_ex(hostname)[2][-1]

        sock = socket.socket()
        sock.bind((ip_addr, 0))
        free_sock = sock.getsockname()[1]
        
        self.central_client_socket.send("login".encode())
        self.userName = userName
        self.password = password
        self.ip_addr = str(ip_addr)
        self.port = 80
        self.Encoder = Encode(self.ip_addr, self.port) # Initialize Encoder
    
        # Server-side Validation
        data = str(self.userName + "," + self.password+","+self.ip_addr+","+str(self.port))

        self.central_client_socket.send(data.encode())
        processStatus = self.central_client_socket.recv(1024).decode()
        print(processStatus)
        if processStatus != 'Kết nối thành công - 1':
            #messagebox.showerror(title="Lỗi đăng kí",message="Username đã được sử dụng hoặc lỗi server. Hãy thử lại.")
            return False
        else:
            # Launch Peer Server to Handle Incomminng Connection
            self.HandleConnection =  PeerServer(self.userName,self.ip_addr, self.port)
            self.HandleConnection.daemon=True
            self.HandleConnection.start()
            # Start Checking Attendance
            global START_CHECKING 
            START_CHECKING = True
            self.startTime = time.time()
            return True
        
        
# This is Server Side of The Peer
# This will contain an Array of All Client Connection
# This Will Act As A Chat Room
class PeerServer(threading.Thread):
    ClientList = [] # List Of Client Connection IP:Connection 
    peerIP = None
    peerPort = None
    def __init__(self, peerName, peerIp, peerPort) -> None:
        threading.Thread.__init__(self)
        self.CliendList = []
        self.peerName = peerName
        self.peerIP = peerIp
        self.listenPort = 80 # change this for each peer if run locally

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((peerIp, int(self.listenPort)))


    def run(self):
        self.server.listen(100)
        print("Start Listening on Port: {}".format(self.listenPort))
        inputs = [self.server]

        while(inputs):
            try:
                readable, writable, exceptional = select.select(inputs, [], [])
                for s in readable:
                    if s is self.server:
                        
                            conn, addr = s.accept()
                            opponent_name = conn.recv(1024).decode(FORMAT)
                            conn.send("Thành công".encode(FORMAT))
                            print(conn)
                            """ conn.bind((self.peerIP,0))   """
                            self.createClientThread(conn,addr[0],addr[1],opponent_name)
                            self.ClientList.append(conn)
                    else:
                        print("Stuck Here")
            except Exception as e:
                print(e)

    def createClientThread(self,conn,cliIP, cliPort,opponent_name) :
        # Create A Thread For Handle That Connection
        # May be a new window
        PeerClient(str(self.peerName),conn,cliIP,cliPort,opponent_name).start()
        self.CliendList.append(conn)
    def sendToAll(self,conn):
        pass
    def closeConn(self,conn):
        pass
    def getConn(self, conn):
        pass

# This is Client Side Of the Peer
# Request and send Message Chat to Other Peer
# This handle Each Connection
# This Class Maybe Handle Transfer
class PeerClient(threading.Thread):
     # constructor method
    def __init__(self, name,conn,ip,port,opponent_name):
        threading.Thread.__init__(self)
        # chat window which is currently hidden
        self.name = name
        self.conn = conn
        self.cip = ip
        self.port = port
        self.opponent_name = opponent_name
        self.Encoder = Encode(ip,port)
        self.running = True

    def run(self) :
        self.Window = Tk()
        self.Window.withdraw()
        self.goAhead(self.name)
        self.Window.protocol("WM_DELETE_WINDOW",  self.onClose)
        self.Window.mainloop()
    
    def goAhead(self, name):
        self.layout(name)
        # the thread to receive messages
        rcv = threading.Thread(target=self.receive)
        rcv.start()
 
    # The main layout of the chat 57A1F8
    def layout(self, name):
        self.name = name
        # to show chat window
        self.Window.deiconify()
        self.Window.title("CHATROOM")
        self.Window.resizable(width=True,
                              height=False)
        self.Window.configure(width=470,
                              height=550,
                              bg="#57A1F8")
        # Head of The Chat
        self.labelHead = Label(self.Window,
                               bg="#17202A",
                               fg="#EAECEE",
                               text=self.opponent_name,
                               font="Helvetica 13 bold",
                               pady=5)
 
        self.labelHead.place(relwidth=1)
        self.line = Label(self.Window,
                          width=450,
                          bg="#ABB2B9")
 
        self.line.place(relwidth=1,
                        rely=0.07,
                        relheight=0.012)
        # Chat Message
        self.textCons = Text(self.Window,
                             width=20,
                             height=2,
                             bg="#17202A",
                             fg="#EAECEE",
                             font="Helvetica 12",
                             padx=20,
                             pady=5,
                             )
 
        self.textCons.place(relheight=0.745,
                            relwidth=1,
                            rely=0.08)
                            
        self.textCons.tag_config("send",foreground="green"
                                ,justify=RIGHT) # Tag to change color
        

        self.labelBottom = Label(self.Window,
                                 bg="#ABB2B9",
                                 height=80)
 
        self.labelBottom.place(relwidth=1,
                               rely=0.825)
        # Enter Message box
        self.entryMsg = Entry(self.labelBottom,
                              bg="#2C3E50",
                              fg="#EAECEE",
                              font="Helvetica 11")
 
        # place the given widget
        # into the gui window
        self.entryMsg.place(relwidth=0.74,
                            relheight=0.06,
                            rely=0.008,
                            relx=0.011)
 
        self.entryMsg.focus()
 
        # create a Send Button
        self.buttonMsg = Button(self.labelBottom,
                                text="Send",
                                font="Helvetica 10 bold",
                                width=20,
                                bg="#ABB2B9",
                                command=lambda: self.sendButton(self.entryMsg.get()))
 
        self.buttonMsg.place(relx=0.77,
                             rely=0.008,
                             relheight=0.03,
                             relwidth=0.22)

        # create a Send Button
        self.buttonSendFile = Button(self.labelBottom,
                                text="File",
                                font="Helvetica 10 bold",
                                width=20,
                                bg="#ABB2B9",
                                command=lambda: self.sendFileButton())
 
        self.buttonSendFile.place(relx=0.77,
                             rely=0.038,
                             relheight=0.03,
                             relwidth=0.22)
 
        self.textCons.config(cursor="arrow")
 

        self.textCons.config(state=DISABLED)
 
    # function to basically start the thread for sending messages
    def sendButton(self, msg):
        self.textCons.config(state=DISABLED)
        self.msg = msg
        self.entryMsg.delete(0, END)
        snd = threading.Thread(target=self.sendMessage)
        snd.start()

    def sendFileButton(self):
        self.textCons.config(state=DISABLED)
        snd = threading.Thread(target=self.sendFile)
        snd.start()
 
    def displayMessage(self,msg, send=False):
        self.textCons.config(state=NORMAL)
        if(send):
            self.textCons.insert(END,
                                    msg+"\n\n","send")
        else:
             self.textCons.insert(END,
                                    msg+"\n\n")

        self.textCons.config(state=DISABLED)
        self.textCons.see(END)
     


    # function to receive messages 
    # This will handle request send from user
    def receive(self):
        while self.running:
            try:
                message = self.conn.recv(1024).decode(FORMAT)
                message = json.loads(message)
                # If message is request message
                if message['type'] == 'Request':
                    # If it is Start Chat Request
                    if message['flag'] == "S":
                        # Call UIn
                        diaglogResult = messagebox.askokcancel("There is Message Request","{} requested chat. Accept?".format(self.opponent_name))
                        if(diaglogResult):
                            self.conn.send(self.Encoder.acceptChat())
                        else:
                            self.conn.send(self.Encoder.declineChat())
                            self.Window.destroy()
                    elif message['flag'] == "E":
                        messagebox.showwarning("Your peer ","{} has left the conversation. The chatbox will be closed after 2 seconds".format(self.name))
                        time.sleep(2)
                        self.running=False
                        self.Window.destroy()
                        
                elif  message['type'] == 'M':
                    # insert messages to text box
                    self.displayMessage(self.opponent_name+" ("+message["time"]+"): "+message['msg'])

                elif message['type'] == 'F':
                    filename = message['fname']
                    filesize = message['fsize']
                    filepath = askdirectory()+ '/' + filename
                    with open(filepath, 'wb') as f:
                        i = 0
                        l = int((filesize-1) / 1024) + 1
                        print(l)
                        while i < l:
                            bytes_read = self.conn.recv(1024)
                            if not bytes_read:
                                break
                            f.write(bytes_read)
                            i += 1

                    self.displayMessage("("+message["time"]+"): Received "+message['fname'])
            except:
                # an error will be printed on the command line or console if there's an error
                print("An error occurred!")


    # function to send exit
    def onClose(self):
        self.Window.destroy()
        self.conn.send(self.Encoder.closeChat())
        self.running = False
        
    # function to send messages
    def sendMessage(self):
        self.textCons.config(state=DISABLED)
        while self.running and self.msg != "":
            #############
            message = (f"{self.msg}")
            self.displayMessage(self.msg, send=True)        
            self.conn.send(self.Encoder.sendMessage(message))
            break

    # function to send files
    def sendFile(self):
        
        self.textCons.config(state=DISABLED)
        filepath = askopenfilename()
        filesize = int(os.path.getsize(filepath))
        filename = filepath.split("/")[-1]
        self.conn.send(self.Encoder.sendFileRequest(filename, filesize))     

        with open(filepath, 'rb') as f:
            while True:
                try:
                    bytes_read = f.read(4096)
                    if not bytes_read:
                        break
                    self.conn.sendall(bytes_read)
                except:
                    break

        self.displayMessage("You have sent file", send=True)        


def printOnlineUsers(data):
    print ("\n<<< ONLINE USER LIST >>>\r")
    print(data)
                
if __name__ == "__main__":
    # [ip,port] = input("IP Port: ").strip().split(" ")
    # Peer(ip,int(port)).run()
    # peer_central = Peer_Central()
    # peer_central.run()
    pass        # có UI gọi những gì liên quan tới peer rồi nên chỗ này ko cần chạy mấy cái peer nữa
    #[ip,port] = input("IP Port: ").strip().split(" ")
    # ip = socket.gethostbyname(socket.gethostname())
    #Peer(ip,int(port)).run()