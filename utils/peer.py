import threading
import socket, select
from tkinter import *
from tkinter import font
from tkinter import ttk
from tkinter import messagebox
import sys,json
from protocol import Encode

FORMAT = "utf-8"


# This is Server Side of The Peer
# This will contain an Array of All Client Connection
# This Will Act As A Chat Room
class PeerServer(threading.Thread):
    ClientList = [] # List Of Client Connection IP:Connection 
    peerIP = None
    peerPort = None
    def __init__(self,peerIp,peerPort) -> None:
        threading.Thread.__init__(self)
        self.CliendList = []
        self.peerIP = peerIp
        self.listenPort = peerPort

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((peerIp, self.listenPort))


    def run(self):
        self.server.listen(100)
        print("Start Listening on Port: {}".format(self.listenPort))
        inputs = [self.server]

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Comment This one To act as Client because Server Thread will Take place std in
        while(inputs):
            try:
                readable, writable, exceptional = select.select(inputs, [], [])
                for s in readable:
                    if s is self.server:
                            conn, addr = s.accept()
                            self.createClientThread(conn,addr[0],addr[1])
                            self.ClientList.append(conn)
                    else:
                        print(s)
            except Exception as e:
                print(e)

    def createClientThread(self,conn,cliIP, cliPort) :
        # Create A Thread For Handle That Connection
        # May be a new window
        print(conn)
        PeerClient(self.peerIP,conn,cliIP,cliPort).start()
        self.CliendList.append(conn)
        pass
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
    def __init__(self, name,conn,ip,port):
        threading.Thread.__init__(self)
        # chat window which is currently hidden
        self.name = name
        self.conn = conn
        self.cip = ip
        self.port = port
        self.Encoder = Encode(ip,port)



    def run(self) :
        self.Window = Tk()
        self.Window.withdraw()
        self.goAhead(self.name)
        self.Window.mainloop()
    
    

    def goAhead(self, name):
        self.layout(name)
        # the thread to receive messages
        rcv = threading.Thread(target=self.receive)
        rcv.start()
 
    # The main layout of the chat
    def layout(self, name):
 
        self.name = name
        # to show chat window
        self.Window.deiconify()
        self.Window.title("CHATROOM")
        self.Window.resizable(width=False,
                              height=False)
        self.Window.configure(width=470,
                              height=550,
                              bg="#17202A")
        self.labelHead = Label(self.Window,
                               bg="#17202A",
                               fg="#EAECEE",
                               text=self.name,
                               font="Helvetica 13 bold",
                               pady=5)
 
        self.labelHead.place(relwidth=1)
        self.line = Label(self.Window,
                          width=450,
                          bg="#ABB2B9")
 
        self.line.place(relwidth=1,
                        rely=0.07,
                        relheight=0.012)
 
        self.textCons = Text(self.Window,
                             width=20,
                             height=2,
                             bg="#17202A",
                             fg="#EAECEE",
                             font="Helvetica 14",
                             padx=5,
                             pady=5)
 
        self.textCons.place(relheight=0.745,
                            relwidth=1,
                            rely=0.08)
 
        self.labelBottom = Label(self.Window,
                                 bg="#ABB2B9",
                                 height=80)
 
        self.labelBottom.place(relwidth=1,
                               rely=0.825)
 
        self.entryMsg = Entry(self.labelBottom,
                              bg="#2C3E50",
                              fg="#EAECEE",
                              font="Helvetica 13")
 
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
                             relheight=0.06,
                             relwidth=0.22)
 
        self.textCons.config(cursor="arrow")
 
        # create a scroll bar
        scrollbar = Scrollbar(self.textCons)
 
        # place the scroll bar
        # into the gui window
        scrollbar.place(relheight=1,
                        relx=0.974)
 
        scrollbar.config(command=self.textCons.yview)
 
        self.textCons.config(state=DISABLED)
 
    # function to basically start the thread for sending messages
    def sendButton(self, msg):
        self.textCons.config(state=DISABLED)
        self.msg = msg
        self.entryMsg.delete(0, END)
        snd = threading.Thread(target=self.sendMessage)
        snd.start()
 
    def displayMessage(self,msg):
        self.textCons.config(state=NORMAL)
        self.textCons.insert(END,
                                msg+"\n\n")

        self.textCons.config(state=DISABLED)
        self.textCons.see(END)
     


    # function to receive messages 
    # This will handle request send from user
    def receive(self):
        while True:
            try:
                message = self.conn.recv(1024).decode(FORMAT)
                message = json.loads(message)
                # If message is request message
                if message['type'] == 'Request':
                    # If it is Start Chat Request
                    if message['flag'] == "S":
                        # Call UIn   
                        diaglogResult = messagebox.askokcancel("There is Message Request","nah")
                        if(diaglogResult == "yes"):
                            self.conn.send(self.Encoder.acceptChat())
                        else:
                            self.conn.send(self.Encoder.declineChat())
                            self.Window.destroy()
                elif  message['type'] == 'M':
                    # insert messages to text box
                    self.displayMessage("("+message["time"]+"):"+message['msg'])
            except:
                # an error will be printed on the command line or console if there's an error
                print("An error occurred!")
                self.conn.close()
                break
 
    # function to send messages
    def sendMessage(self):
        self.textCons.config(state=DISABLED)
        while True:
            message = (f"{self.name}: {self.msg}")           
            self.conn.send(self.Encoder.sendMessage(message))
            break



# This is The Peer Main Class act as A routing
# It will contain Server side and Client Side
# This peer will listen request sent from other Peer

class Peer:

    def __init__(self,peerIp, peerPort) -> None:
        self.peerIp = peerIp
        self.peerPort = peerPort
        self.Encoder = Encode(self.peerIp, self.peerPort)

        UI = threading.Thread(target=self.runUI)
        UI.start()
        self.HandleConnection=PeerServer(peerIp,peerPort)
        self.HandleConnection.daemon=True
        self.HandleConnection.start()
    


    def run(self):
        while(True):
            choose = input("Enter Your Choose")
            if(choose == "1" ):
                [ip,port] = input("Connect to IP Port: ").strip().split(" ")
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.connect((ip, int(port)))

                conn.send(self.Encoder.requestChat())

                msg = conn.recv(1024).decode(FORMAT)
                msg = json.loads(msg)
                if(msg['code']==1):
                    self.HandleConnection.createClientThread(conn,ip,port)
                else:
                    print("Peer Decline Chat")


    # This is for testing purpose
    def runUI(self): 
        self.Window = Tk()
        self.Window.withdraw()
        self.goAhead("Haha")
        self.Window.mainloop()

    def goAhead(self, name):
        self.layout(name)
        # the thread to receive messages
 
    # The main layout of the chat
    def layout(self, name):
 
        self.name = name
        # to show chat window
        self.Window.deiconify()
        self.Window.title("Hello User {}".format(self.peerIp))

        self.Window.configure(width=470,
                              height=150,
                              bg="#17202A")
                              
        self.labelBottom = Label(self.Window,
                                 bg="#ABB2B9",
                                 height=80)
 
        self.labelBottom.place(relwidth=1,
                               rely=0)
 
        self.entryMsg = Entry(self.labelBottom,
                              bg="#2C3E50",
                              fg="#EAECEE",
                              font="Helvetica 13")
 
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
                             relheight=0.06,
                             relwidth=0.22)
 
    # function to basically start the thread for sending messages
    def sendButton(self, msg):
        self.msg = msg
        self.entryMsg.delete(0, END)
        [ip,port] = self.msg.strip().split(" ")
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((ip, int(port)))
        conn.send(Encode.requestChat())
        conn.recv(1024)
        self.HandleConnection.createClientThread(conn,ip,port)


if __name__ == "__main__":
    [ip,port] = input("IP Port: ").strip().split(" ")
    # ip = socket.gethostbyname(socket.gethostname())
    Peer(ip,int(port)).run()


