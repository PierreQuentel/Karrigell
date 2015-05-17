import sys
import os

# modify sys.path to use this version of Karrigell
cwd = os.getcwd()
sys.path.insert(0,os.path.join(os.path.dirname(cwd),'trunk'))

import Karrigell
import Karrigell.sessions
# also import HTMLTags, so that the name "HTMLTags" will be in 
# sys.modules when Karrigell imports it
import HTMLTags

import threading
import unittest
import urllib.request
import http.cookies

class TestServer(threading.Thread):

    def __init__(self,**kw):
        self.kw = kw
        threading.Thread.__init__(self)

    def run(self,**kw):
        Karrigell.run(**self.kw)

class Tester(unittest.TestCase):

    def test_not_found(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            res = urllib.request.urlopen(self.start+"/xyz.azert")
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 404)

    def test_echo(self):
        res = urllib.request.urlopen(self.start+"/test.py/hello?name=tartampion")
        self.assertEqual(res.read(),b'Hello tartampion')

    def test_import(self):
        res = urllib.request.urlopen(self.start+"/test.py/import_test")
        self.assertEqual(res.read(),b'<b>foobar</b>')

    def test_cookie(self):
        res = urllib.request.urlopen(self.start+"/test.py/set_cookie?name=band&val=smiths")
        info = res.info()
        self.assertIn('set-cookie',info)
        cookie = info['set-cookie'].split('=')
        self.assertEqual(cookie[0],"band")
        req = urllib.request.Request(self.start+"/test.py/read_cookie?name=band")
        req.add_header('Cookie',"=".join(cookie))
        res = urllib.request.urlopen(req)
        self.assertEqual(res.read(),b'smiths')

    def test_pep0263(self):
        # test handling of source encoding as defined by PEP 0263
        data = open('text_for_pep0263_tests.txt','rb').read()
        res = urllib.request.urlopen(self.start+"/test_pep0263_line.py/index")
        self.assertEqual(res.read(),data)
        res = urllib.request.urlopen(self.start+"/test_pep0263_bom.py/index")
        self.assertEqual(res.read(),data)
        res = urllib.request.urlopen(self.start+"/test_pep0263_line_wrong_encoding.py/index")
        self.assertIn(b'Karrigell.ScriptError',res.read())

class SessionTester(unittest.TestCase):

    def test_session(self):
        res = urllib.request.urlopen(self.start+"/test.py/set_session?name=shelley")
        info = res.info()
        self.assertIn('set-cookie',info)
        cookie = info['set-cookie'].split('=')
        self.assertEqual(cookie[0],"session_id")
        session_id = cookie[1]
        req = urllib.request.Request(self.start+"/test.py/get_session")
        req.add_header('Cookie',"=".join(cookie))
        res = urllib.request.urlopen(req)
        self.assertEqual(res.read(),b'shelley')

class AppMemorySession(Karrigell.App):

    session_storage_class = Karrigell.sessions.MemorySessionStorage
    
class AppFileSession(Karrigell.App):

    session_storage_class = Karrigell.sessions.FileSessionStorage

class AppFilter(Karrigell.App):

    hidden = ['.sqlite']
    # test with extra app
    def hide_ext(self,handler):
        for ext in self.hidden:
            if handler.path_info.endswith(ext):
                raise Karrigell.HTTP_ERROR(403)
    filters = [hide_ext]

# test with default app
server = TestServer(port=8082)
server.start()

# test with filtering app
server = TestServer(apps=[AppFilter],port=8083)
server.start()

# test with memory session storage
server = TestServer(apps=[AppMemorySession],port=8084)
server.start()

# test with file session storage
server = TestServer(apps=[AppFileSession],port=8085)
server.start()

class Tester1(Tester,SessionTester):
    start = "http://localhost:8082"

class Tester2(Tester):
    start = "http://localhost:8083"

    def test_filter(self):
        # check that files with extension sqlite are forbidden
        with self.assertRaises(urllib.error.HTTPError) as cm:
            res = urllib.request.urlopen(self.start+"/truc.sqlite")
        the_exception = cm.exception
        self.assertEqual(the_exception.code, 403)

class Tester3(SessionTester):
    start = "http://localhost:8084"

class Tester4(Tester,SessionTester):
    start = "http://localhost:8085"

suite = unittest.TestSuite()
for test in Tester1,Tester2,Tester3,Tester4:
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(test))
unittest.TextTestRunner(verbosity=1).run(suite)
