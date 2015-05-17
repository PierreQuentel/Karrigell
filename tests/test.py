a = 'jkl'

def index(**kw):
    res = 'Received cookies'
    for cookie in COOKIE:
        res += cookie+' '+COOKIE[cookie].value
    res += '<p>Role %s' %COOKIE.get('Role',None)
    f = FORM(action='set_session')
    f <= INPUT(name="name")
    f <= INPUT(Type="submit",value="Ok")
    res += f+P()
    res += BR()+A('Get session',href='get_session')
    return res

def hello(name):
    return "Hello %s" %name
    
def bar(name):
    SET_COOKIE['role'] = name
    SET_COOKIE['role']['path'] = '/'
    return Template('page.tmpl',title='template test',name=name)

def import_test():
    module = Import('imported.py')
    return module.data

def sels(name):
    return name

def upload2(src):
    import mimetypes
    gtype,encoding = mimetypes.guess_type(src.filename)
    RESPONSE_HEADERS['content-type'] = gtype
    return src.file.read()

def set_session(name):
    Session()['name']=name

def get_session():
    return Session()['name']

def set_cookie(name,val):
    SET_COOKIE[name] = val

def read_cookie(name):
    return COOKIE[name].value

def see():
    import sqlite3
    conn = sqlite3.connect('sessions.sqlite')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sessions')
    return cursor.fetchall()