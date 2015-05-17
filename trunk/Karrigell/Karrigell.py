"""Karrigell server and request handler

Python scripts are executed in a namespace made of :
- REQUEST_HEADERS : the http request headers sent by user agent
- COOKIE : cookies sent by user agent
- RESPONSE_HEADERS : the http response headers
- SET_COOKIE : used to set cookies for user agent
- ENCODING : determines the Unicode encoding used by user agent
- Template(url,encoding,*args,**kw) : return the file at specified url, uses
  standard Python string formatting (method format() for strings)
- HTTP_REDIRECTION : an exception to raise if the script wants to redirect
to a specified URL : raise HTTP_REDIRECTION(url)
- Import() : replacement for built-in import for user-defined modules
- Session() : a function returning the session object
- THIS : instance of the request handler
"""

import sys
import os
import shutil
import re
import string
import io
import random
import traceback
import types
import datetime
import gzip

import socket
import socketserver
import urllib.parse
import cgi
import http.server
import http.cookies
import email.utils
import email.message

import Karrigell.sessions
import Karrigell.admin_db as admin_db

version = "4.3.10"

class HTTP_REDIRECTION(Exception):
    pass

class HTTP_ERROR(Exception):

    def __init__(self,code,message=None):
        self.code = code
        self.message = message

class ScriptError(Exception):
    pass

class ImageInput:
     pass 

class RequestHandler(http.server.CGIHTTPRequestHandler):
    """One instance of this class is created for each HTTP request"""

    name = 'Karrigell'
    
    def do_GET(self):
        """Begin serving a GET request"""
        # build self.body from the query string
        self.elts = urllib.parse.urlparse(self.path)
        data = urllib.parse.parse_qs(self.elts[4], keep_blank_values=1)
        self.body = {}
        for key in data:
            if key.endswith('[]'):
                self.body[key[:-2]] = data[key]
            else:
                self.body[key] = data[key][0]
        self.handle_data()

    def do_POST(self):
        """Begin serving a POST request"""
        self.elts = urllib.parse.urlparse(self.path)
        body = cgi.FieldStorage(self.rfile,headers=self.headers,
            environ={'REQUEST_METHOD':'POST'}) # read POST data from self.rfile
        data = {}
        # If field name ends with [], always return a list of values
        # Otherwise, return a value, or the item with attributes
        # 'file' and 'filename' for file uploads
        for k in body.keys():
            if isinstance(body[k],list): # several fields with same name
                if k.endswith('[]'):
                    data[k[:-2]] = [x.value for x in body[k]]
            else:
                if body[k].filename: # file upload : don't read the value
                    data[k] = body[k]
                else:
                    if k.endswith('[]'):
                        data[k[:-2]] = [body[k].value]
                    else:
                        if '.' in k : 
                            # if field is <input type="image" name="foo"> 
                            # then data has keys foo.x and foo.y
                            n,a = k.split('.')
                            try :
                                setattr(data[n], a, body[k].value)
                            except KeyError:
                                data[n] = ImageInput()
                                setattr(data[n], a, body[k].value)
                        else:
                            data[k] = body[k].value 
        self.body = data
        self.handle_data()

    def handle_data(self):
        """Process the data received"""
        # received cookies
        self.cookies = http.cookies.SimpleCookie(self.headers.get("cookie",None))
        # initialize response headers and cookies
        self.resp_headers = email.message.Message()
        self.resp_headers.add_header("Content-type",'text/html') # default
        self.set_cookie = http.cookies.SimpleCookie() # cookies to return to user
        self.encoding = sys.getdefaultencoding() # Unicode encoding
        
        self.path_info = self.elts[2] # equivalent of CGI PATH_INFO
        elts = urllib.parse.unquote(self.path_info).split('/')
        # identify the application and set attributes from it
        host = (urllib.parse.urlparse("http://"+self.headers.get("host",None)).hostname) 
        if (host, elts[1]) in self.alias:
            app = self.alias[(host, elts[1])]
        elif (host, '') in self.alias:
            app = self.alias[(host, '')]
        else:
            return self.send_error(404,'Unknown alias '+elts[1])
        self.app = app
        for attr in ['root_url','root_dir','users_db']:
            setattr(self,attr,getattr(app,attr))
        self.login_url = app.get_login_url()
        self.session_storage = None
        if app.session_storage:
            self.session_storage = app.session_storage
        self.login_cookie,self.skey_cookie = app.get_cookie_names()
        
        # apply application filters
        filtered = None
        for func in app.filters:
            try:
                filtered = func(app,self) or filtered
            except HTTP_REDIRECTION as url:
                redir_to = str(url)
                return self.redir(redir_to)
            except HTTP_ERROR as msg:
                return self.send_error(msg.code,msg.message)
            except:
                return self.print_exc()
        # if no filter returned a value other than None, use default
        fs_path = filtered or self.get_file(self.elts[2])
        elts = list(self.elts)
        if os.path.isdir(fs_path):  # url matches a directory
            if not elts[2].endswith('/'):
                elts[2] += '/'
                return self.redir(urllib.parse.urlunparse(elts))
            if os.path.exists(os.path.join(fs_path,'index.py')):
                elts[2] += 'index.py/index'
                return self.redir(urllib.parse.urlunparse(elts))
            elif os.path.exists(os.path.join(fs_path,'index.html')):
                elts[2] += 'index.html'
                return self.redir(urllib.parse.urlunparse(elts))
            else:  # list directory
                dir_list = self.list_directory(fs_path) # send resp + headers
                return self.copyfile(dir_list, self.wfile)
        ext = os.path.splitext(fs_path)[1].lower()
        if ext.lower()=='.py':
            # redirect to function index of script
            elts[2] += '/index'
            return self.redir(urllib.parse.urlunparse(elts))
        script_path,func = fs_path.rsplit(os.sep,1)
        if os.path.splitext(script_path)[1] == '.py':
            # Python script called with a function name
            self.url_path = elts[2]
            self.script_path = script_path
            try:
                self.run(func)
            except:
                return self.print_exc()
        else: # other files than Python scripts
            try:
                f = open(fs_path,'rb')
            except IOError:
                return self.send_error(404, "File not found")
            # use browser cache if possible
            if "If-Modified-Since" in self.headers:
                ims = email.utils.parsedate(self.headers["If-Modified-Since"])
                if ims is not None:
                    ims_datetime = datetime.datetime(*ims[:7])
                    ims_dtstring = ims_datetime.strftime("%d %b %Y %H:%M:%S")
                    last_modif = datetime.datetime.utcfromtimestamp(
                        os.stat(fs_path).st_mtime).strftime("%d %b %Y %H:%M:%S")
                    if last_modif == ims_dtstring:
                        return self.done(304,io.BytesIO())
            ctype = self.guess_type(fs_path)
            self.resp_headers.replace_header('Content-type',ctype)
            self.resp_headers["Last-modified"] = \
                self.date_time_string(os.stat(fs_path).st_mtime)
            # zip ?
            accept_encoding = self.headers.get('accept-encoding','').split(',')
            accept_encoding = [ x.strip() for x in accept_encoding ]
            # if gzip is supported by the user agent, and content type is text
            # or javascript, use gzip compression
            if 'gzip' in accept_encoding and ctype and \
                (ctype.startswith('text/') 
                    or ctype=='application/x-javascript'):
                    sio = io.BytesIO()
                    gzf = gzip.GzipFile(fileobj=sio,mode="wb")
                    shutil.copyfileobj(f,gzf)
                    self.resp_headers['Content-length'] = gzf.tell()
                    self.resp_headers["Content-Encoding"] = "gzip"
                    gzf.close()
                    sio.seek(0)
                    self.done(200,sio)
            else:
                self.resp_headers['Content-length'] = str(os.fstat(f.fileno())[6])
                self.done(200,f)

    def redir(self,url):
        # redirect to the specified url
        self.close_connection = True
        self.resp_headers['Location'] = url
        self.done(302,io.BytesIO())

    def get_file(self,path):
        """Return a file name matching path"""
        if self.root_url == '/':
            elts = urllib.parse.unquote(path).split('/')
        else:
            elts = urllib.parse.unquote(path[len(self.root_url):]).split('/')
        return os.path.join(self.root_dir,*elts)

    def erase_cookie(self,name):
        self.set_cookie[name] = ''
        self.set_cookie[name]['path'] = self.root_url
        new = datetime.date.today() + datetime.timedelta(days = -10) 
        self.set_cookie[name]['expires'] = \
            new.strftime("%a, %d-%b-%Y 23:59:59 GMT")
        self.set_cookie[name]['max-age'] = 0

    def login(self,role='admin',login_url=None,origin=None):
        """If user is logged in with specified role, do nothing, else
        redirect to login_url"""
        login_url = login_url or self.login_url
        origin = origin or self.path
        if not self.users_db:
            raise HTTP_ERROR(500,"Can't login, no users database set")
        args = {'role':role,'origin':origin}
        qs = urllib.parse.urlencode(args)
        if not self.skey_cookie in self.cookies:
            raise HTTP_REDIRECTION(login_url+'?'+qs)
        skey = self.cookies[self.skey_cookie].value
        if not self.users_db.key_has_role(skey,role):
            raise HTTP_REDIRECTION(login_url+'?'+qs)

    def logout(self,redir_to=None):
        """Log out = erase login and session key cookies, then redirect"""
        redir_to = redir_to or urllib.parse.urljoin(self.path_info,'index')
        self.erase_cookie(self.login_cookie)
        self.erase_cookie(self.skey_cookie)
        raise HTTP_REDIRECTION(redir_to)

    def user(self):
        if self.users_db is None:
            return None
        if not self.skey_cookie in self.cookies:
            return False
        skey = self.cookies[self.skey_cookie].value
        return self.users_db.get_user(skey=skey)

    def abs_path(self,*rel_path):
        """Return absolute path in the file system, relative to script path"""
        return os.path.join(os.path.dirname(self.script_path),*rel_path)

    def abs_url(self,*rel_url):
        base = self.url_path
        return urllib.parse.urljoin(base[:base.rfind('/')],*rel_url)

    def source(self,script_path):
        # manages encoding of Python source code (PEP 0263)
        src_enc = "utf-8" # default (PEP 3120)
        enc_msg = "Default encoding utf-8"
        src = open(script_path,'rb')
        head = src.read(3)
        if not head == b'\xef\xbb\xbf': # BOM for utf-8
            head = ''
            src.seek(0)
            first2lines = [src.readline(),src.readline()]
            for line in first2lines:
                mo = re.search(b"coding[:=]\s*([-\w.]+)",line)
                if mo:
                    src_enc = mo.groups()[0].decode('ascii')
                    enc_msg = 'Declared encoding "%s"' %src_enc
                    break
        src.seek(len(head))
        try:
            for n,line in enumerate(src):
                line.rstrip().decode(src_enc)
            # if encoding is correct, return bytes
            src.seek(0)
            return src.read()
        except UnicodeDecodeError as exc:
            msg = "Encoding error in file %s\n" %script_path
            msg += enc_msg
            msg += " but there are non-%s characters in line %d" %(src_enc,n+1)
            raise ScriptError(msg) from exc 

    def run(self,func):
        """Run function func in a Python script
        Function arguments are key/values in request body or query string"""
        # initialize script execution namespace
        self.namespace = {'REQUEST_HEADERS' : self.headers,
            'ACCEPTED_LANGUAGES':self.headers.get("accept-language",None),
            'RESPONSE_HEADERS':self.resp_headers,
            'HTTP_REDIRECTION':HTTP_REDIRECTION,
            'HTTP_ERROR':HTTP_ERROR,
            'COOKIE':self.cookies,'SET_COOKIE':self.set_cookie,
            'ENCODING':self.encoding,
            'Session':self.Session,
            'Logout':self.logout,'Login':self.login,'User':self.user,
            'Import':self._import,'THIS': self }
        # import names from HTMLTags
        import HTMLTags
        for k in dir(HTMLTags):
            if not k.startswith('_'):
                self.namespace[k] = getattr(HTMLTags,k)
        # Add KT wrapper function to the namespace
        import Karrigell.KT
        def KT(encoding=self.encoding, translate=str):
            return Karrigell.KT.KT(encoding=encoding,
                    translate=translate, handler=self)
        self.namespace['KT'] = KT
        self.imported_modules = [] # stack of imported modules, for traceback
        
        src = self.source(self.script_path)
        try:
            exec(compile(src,self.script_path,'exec'),
                self.namespace) # run script in namespace
            func_obj = self.namespace.get(func,None)
            if func_obj is None \
                or not isinstance(func_obj,types.FunctionType) \
                or not func_obj.__code__.co_filename==self.script_path \
                or func.startswith('_'):
                    msg = 'No function %s in script %s' \
                        %(func,os.path.basename(self.script_path))
                    self.done(500,io.BytesIO(msg.encode(self.encoding)))
                    return
            # run function with self.body as argument
            result = self.namespace[func](**self.body) # string or bytes
            self.save_session()
        except HTTP_REDIRECTION as url:
            self.save_session()
            return self.redir(url)
        except HTTP_ERROR as msg:
            return self.send_error(msg.code,msg.message)
        encoding = self.namespace['ENCODING']
        if not "charset" in self.resp_headers["Content-type"]:
            if encoding is not None:
                ctype = self.resp_headers["Content-type"]
                self.resp_headers.replace_header("Content-type",
                    ctype + "; charset=%s" %encoding)
        output = io.BytesIO()
        if isinstance(result,bytes):
            output.write(result)
        elif isinstance(result,str):
            try:
                output.write(result.encode(encoding))
            except UnicodeEncodeError:
                msg = io.StringIO()
                traceback.print_exc(file=msg)
                return self.done(500,io.BytesIO(msg.getvalue().encode('ascii')))
        else:
            output.write(str(result).encode(encoding))
            
        self.resp_headers['Content-length'] = output.tell()
        self.done(200,output)

    def print_exc(self):
        # print exception
        self.resp_headers.replace_header('Content-type','text/plain')
        result = io.StringIO()
        if hasattr(self,'imported_modules') and self.imported_modules:
            msg = 'Exception in imported module %s\n' %self.imported_modules
            result.write(msg)
        traceback.print_exc(file=result)
        result = io.BytesIO(result.getvalue().encode('ascii','ignore'))
        self.done(200,result) 

    def _import(self,url):
        """Import by url - in threaded environments, "import" is unsafe
        Returns an object whose names are those of the module at this url"""
        fs_path = self.get_file(self.abs_url(url))
        # save the module name so it can be displayed if there is an exception
        self.imported_modules.append(fs_path)
        # update builtins so that imported scripts use script namespace
        ns = {}
        ns.update(self.namespace)
        src = self.source(fs_path)
        exec(compile(src,fs_path,'exec'),ns)
        # No exception executing imported code, so clear saved module name
        self.imported_modules.remove(fs_path)
        class Imported:
            def __init__(self,ns):
                for k,v in ns.items():
                    setattr(self,k,v)
        return Imported(ns) 

    def Session(self):
        """Get session object matching session_id cookie
        If no session_id cookie was received, generate one and return an
        empty SessionElement instance"""
        if self.session_storage is None:
            raise Exception("No session storage defined")
        if hasattr(self,'session_object'):
            return self.session_object
        if "session_id" in self.cookies:
            self.session_id = self.cookies["session_id"].value
        else:
            chars = string.ascii_letters + string.digits
            self.session_id = ''.join([random.choice(chars) for i in range(16)])
            self.set_cookie["session_id"] = self.session_id
            self.set_cookie["session_id"]["path"] = "/"
        self.session_object = self.session_storage.get(self.session_id)
        return self.session_object

    def save_session(self):
        if self.session_storage:
            self.session_storage.save(self)

    def done(self, code, infile):
        """Send response, cookies, response headers + 
        the *bytes* read from infile"""
        self.send_response(code)
        if code == 500:
            self.resp_headers.replace_header('Content-Type','text/plain')
        for (k,v) in self.resp_headers.items():
            self.send_header(k,v)
        for morsel in self.set_cookie.values():
            self.send_header('Set-Cookie', morsel.output(header='').lstrip())
        self.end_headers()
        infile.seek(0)
        self.copyfile(infile, self.wfile)
        self.wfile.flush()

class App:
    """Application parameters"""    
    root_url = '/'
    login_url = None
    root_dir = os.getcwd()
    session_storage = None
    users_db = None
    filters = []
    # names for login and session key cookies. Should be application specific
    login_cookie = None
    skey_cookie = None
    hosts = ['localhost', '127.0.0.1','::1']

    @classmethod
    def get_login_url(self):
        if self.login_url is not None:
            return self.login_url
        elif self.root_url == '/':
            return '/admin/login.py/login'
        else:
            return self.root_url+'/admin/login.py/login'

    @classmethod
    def get_cookie_names(self):
        suffix = self.root_url.lstrip('/').replace('/','_')
        login_cookie = self.login_cookie or 'login_'+suffix
        skey_cookie = self.skey_cookie or 'skey_'+suffix
        return login_cookie,skey_cookie

def run(handler=RequestHandler,port=80,apps=[App],
    server=socketserver.ThreadingTCPServer, address_family=socket.AF_INET):
    server.address_family=address_family
    import Karrigell.check_apps
    Karrigell.check_apps.check(apps)
    handler.apps = apps
    handler.alias = {}
    for app in apps :
        root_url = app.root_url.lstrip('/')
        for host in app.hosts :
            handler.alias[(host, root_url)] = app
    s=server(('',port),handler)
    print("%s %s running on port %s (%s)" %(handler.name,version,port,
        {socket.AF_INET : "IPV4", socket.AF_INET6 : "IPV6"}[address_family]))
    s.serve_forever()

def run_app(host="http://localhost",*args,**kw):
    """Start the server in a thread, then open a web browser"""
    import threading
    import webbrowser
    class Launcher(threading.Thread):
        def run(self):
            run(*args,**kw)
    Launcher().start()
    webbrowser.open(host)

if __name__=="__main__":
    run()
