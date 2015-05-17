import socket
import asyncore
import asynchat
import email.message
import http.server,http.client
import io
import Karrigell
import Karrigell.check_apps

class Wfile:

    def __init__(self,handler):
        self.handler = handler
    
    def write(self,data):
        self.handler.push(data)
    
    def flush(self):
        pass

class http_request_handler(asynchat.async_chat,Karrigell.RequestHandler):

    def __init__(self, sock, client_address, sessions, log):
        asynchat.async_chat.__init__(self, sock=sock)
        self.client_address = client_address
        self.sessions = sessions
        self.log = log
        self.reset_values()

    def reset_values(self):
        self.ibuffer = []
        self.obuffer = b""
        self.set_terminator(b"\r\n\r\n")
        self.reading_headers = True
        self.handling = False
        self.cgi_data = None
        self.wfile = Wfile(self)

    def collect_incoming_data(self, data):
        """Buffer the data"""
        self.ibuffer.append(data)

    def found_terminator(self):
        if self.reading_headers:
            self.reading_headers = False
            lines = b''.join(self.ibuffer).split(b'\r\n')
            self.requestline = lines.pop(0).decode('ascii')
            self.command,self.path,self.protocol = self.requestline.split()
            self.request_version = self.protocol
            rfile = io.BytesIO(b'\r\n'.join(lines)+b'\r\n\r\n')
            rfile.seek(0)
            self.headers = http.client.parse_headers(rfile)
            self.close_connection = \
                self.headers.get('Connection',None).lower()!="keep-alive"
            self.ibuffer = []
            if self.command.upper() == "POST":
                clen = self.headers.get("content-length")
                self.set_terminator(int(clen))
            else:
                self.handling = True
                self.set_terminator(None)
                self.do_GET()
        elif not self.handling:
            self.set_terminator(None) # browsers sometimes over-send
            self.rfile = io.BytesIO(b"".join(self.ibuffer))
            self.handling = True
            self.ibuffer = []
            self.do_POST()
        if self.close_connection:
            self.close()

class Server(asynchat.async_chat):

    def handle_read(self):
        try:
            sock,client_address = self.socket.accept()
            sock.setblocking(0)
        except socket.error:
            return
        self.handler(sock,client_address,None,None)

def run(handler=http_request_handler,port=80,apps=[Karrigell.App]):
    use_ipv6 = False
    Karrigell.check_apps.check(apps)
    handler.apps = apps
    handler.alias = dict((app.root_url.lstrip('/'),app)
        for app in apps)
    sock = socket.socket((socket.AF_INET, socket.AF_INET6)[use_ipv6],
                              socket.SOCK_STREAM)
    # for 'Address already in use' 
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    sock.setblocking(0)
    sock.bind(('',port))
    sock.listen(5)
    server = Server(sock)
    server.handler = handler
    print("Karrigell asynchronous server running on port {}".format(port))
    asyncore.loop()

if __name__=="__main__":
    run(port=8000)