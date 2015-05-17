import os
import sqlite3
import hashlib
import datetime

levels = {'admin':1000,'edit':500,'visit':100}

class User:

    def __init__(self,login,role):
        self.login = login
        self.role = role
        
class SQLiteUsersDb:

    def __init__(self,path):
        self.path = path
        self.name = path
    
    def setup(self):
        """called by check_apps on server startup"""
        if not os.path.exists(self.path):
            db_dir = os.path.dirname(self.path)
            if not os.path.exists(db_dir):
                msg = "Directory of SQLite database {} doesn't exist"
                raise ValueError(msg.format(db_dir))
            conn = sqlite3.connect(self.path)
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE users (login TEXT,password TEXT,\
                role TEXT, skey TEXT, created TEXT, last_visit TEXT,\
                nb_visits INTEGER)')
            conn.commit()
            conn.close()

    def is_empty(self):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute('SELECT login FROM users')
        return not bool(cursor.fetchall())

    def key_has_role(self,skey,req_role):
        """Test if the database has a user with the session key "skey" 
        and if so, if its role is greater or equal to req_role"""
        if req_role is None:
            return True
        if not req_role in levels:
            fmt = 'Unknow role : {} - must be one of {}'
            raise ValueError(fmt.format(req_role,list(levels.keys())))
        """conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM users WHERE skey=?',(skey,))
        result = cursor.fetchall()"""
        role = self.get_role(skey=skey)
        if not role:
            return False
        else:
            return levels[role] >= levels[req_role]

    def user_has_role(self,login,password,req_role):
        """Test if the database has a user with the specified login
        and password and if so, if its role is greater or equal to req_role"""
        if req_role is not None and not req_role in levels:
            fmt = 'Unknow role : {} - must be one of {}'
            raise ValueError(fmt.format(req_role,list(levels.keys())))
        role = self.get_role(login=login,password=password)
        if role is None: # user not found
            return False
        elif req_role is None: # user found, unspecified required role
            return True
        else: # user found, specified required role
            return levels[role] >= levels[req_role]

    def get_user(self,**kw):
        """Return the role of user with session key skey"""
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        args = []
        for key in kw.keys():
            value = kw[key]
            if key=='password':
                _hash = hashlib.md5()
                _hash.update(value.encode('utf-8'))
                value = _hash.digest()
            args.append(value)
        clause = ' AND '.join(key+'=?' for key in kw.keys())
        cursor.execute('SELECT login,role FROM users WHERE '+clause,args)
        result = cursor.fetchall()
        if not result:
            return None
        else:
            return User(result[0][0],result[0][1])

    def get_role(self,**kw):
        user = self.get_user(**kw)
        if not user:
            return user
        return user.role

    def set_session_key(self,login,skey):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET skey=? WHERE login=?',(skey,login))
        conn.commit()

    def add_user(self,login,password,role):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        _hash = hashlib.md5()
        _hash.update(password.encode('utf-8'))
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('SELECT * FROM users WHERE login=?',(login,))
        if cursor.fetchone():
            raise ValueError('User {} already exists'.format(login))
        cursor.execute('INSERT INTO users (login,password,role,created,last_visit,nb_visits) \
            VALUES (?,?,?,?,?,?)',(login,_hash.digest(),role,now,now,1))
        conn.commit()

    def update_visits(self,skey):
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute('SELECT nb_visits FROM users WHERE skey=?',
            (skey,))
        nb_visits = cursor.fetchone()[0]
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('UPDATE users SET last_visit=?,nb_visits=? WHERE skey=?',
            (now,nb_visits+1,skey))
        conn.commit()

    def get_connection(self):
        return sqlite3.connect(self.path)

