# SSL server
import ssl

import socket
import socketserver

class SSLServer(socketserver.ThreadingTCPServer):

    pem = None # replace by path of .pem file

    def __init__(self, server_address, HandlerClass):
        socketserver.ThreadingTCPServer.__init__(self, 
            server_address, HandlerClass)
        sock = socket.socket(self.address_family,self.socket_type)
        self.socket = ssl.wrap_socket(sock,
            certfile=self.pem,keyfile=self.pem)
        self.server_bind()
        self.server_activate()
