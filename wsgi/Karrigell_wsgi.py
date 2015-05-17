import sys
import os
import datetime
import email
import io

from wsgiref import simple_server,util

import Karrigell

class WSGIHandlerClass(simple_server.WSGIRequestHandler):
    """Logging is managed by Karrigell"""

    def log_message(self,*args):
        return

class Server:
    """Fake server class for interface compatibility"""

    def __init__(self,host,port):
        self.host = host
        self.port = port

class k_handler(Karrigell.RequestHandler):

    def __init__(self,environ):
        """Build Karrigell-specific attributes from the environ
        prepared by the WSGI server"""
        self.server = Server(environ["SERVER_NAME"],environ["SERVER_PORT"])
        self.server_version = environ.get("SERVER_SOFTWARE","unknown server software")

        self.client_address = (environ["REMOTE_ADDR"],0)
        self.rfile = environ['wsgi.input'] # for POST requests
        self.output = io.BytesIO()
        self.wfile = self.output

        # headers
        self.headers = email.message_from_string('')
        if 'CONTENT_TYPE' in environ:
            self.headers['Content-type'] = environ['CONTENT_TYPE']
        if 'CONTENT_LENGTH' in environ:
            self.headers['Content-length'] = environ['CONTENT_LENGTH']
        for k in environ:
            if k.startswith("HTTP_"):
                header = k[5:].replace('_','-')
                self.headers[header] = environ[k]

        self.path = environ["PATH_INFO"]
        if environ["QUERY_STRING"]:
            self.path += '?'+environ["QUERY_STRING"]
        self.request_version = environ["SERVER_PROTOCOL"]
        self.protocol_version = environ["SERVER_PROTOCOL"]
        self.requestline = "%s %s %s" %(environ["REQUEST_METHOD"],
            self.path,environ["SERVER_PROTOCOL"])
        self.command = environ["REQUEST_METHOD"]

    def handle_one_request(self):
        if self.command in ['GET','POST']:
            command = getattr(self,'do_'+self.command)
            command()

    def send_response_only(self, code, message=None):
        """Send the response header only."""
        if message is None:
            if code in self.responses:
                message = self.responses[code][0]
            else:
                message = ''
        self.response = "%d %s" %(code, message)

    def end_headers(self):
        return

    def done(self, code, infile):
        self.send_response_only(code)
        if code == 500:
            self.resp_headers.replace_header('Content-Type','text/plain')
        for morsel in self.set_cookie.values():
            self.resp_headers.add_header('Set-Cookie', morsel.output(header='').lstrip())
        infile.seek(0)
        self.output = infile

class File:
    """Class to manage file objects as iterators
    Used as the return value of WSGI application, to avoid having to
    store the file content in memory"""

    blocksize = 2 << 17

    def __init__(self,fileobj):
        self.fileobj = fileobj
        self.fileobj.seek(0)

    def __iter__(self):
        return self
        
    def __next__(self):
        buf = self.fileobj.read(self.blocksize)
        if not buf:
            raise StopIteration
        return buf

class App(Karrigell.App):
    root_dir = os.path.dirname(__file__)

apps = [App]

def application(environ,start_response):
    handler = k_handler(environ)
    handler.alias = {'':App}
    handler.handle()
    resp_headers = [(k,str(v)) for (k,v) in handler.resp_headers.items() ]
    start_response(handler.response, resp_headers)
    return File(handler.output)

if __name__ == "__main__":
    httpd = simple_server.make_server('', 8000, application,
        handler_class=WSGIHandlerClass)
    sa = httpd.socket.getsockname()
    print("Serving HTTP on", sa[0], "port", sa[1], "...")
    httpd.serve_forever()
