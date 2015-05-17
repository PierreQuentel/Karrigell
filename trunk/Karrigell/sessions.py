import os
import pickle
import marshal
import sqlite3
import traceback
import threading
import datetime

class SessionElement(dict):

    def __init__(self,restricted = True):
        dict.__init__(self)
        self.restricted = restricted

    def __setitem__(self,key,value):
        if self.restricted:
            # test that value is a Python built-in type
            try:
                marshal.dumps(value)
            except ValueError:
                msg = 'Bad type for session object key %s ' %key
                msg += ': expected built-in type, got %s' %value.__class__
                raise ValueError(msg)
        dict.__setitem__(self,key,value)

class MemorySessionStorage:

    sessions = {}

    def save(self,handler):
        """Save session object as a dictionary"""
        if hasattr(handler,'session_object'):
            self.sessions[handler.session_id] = handler.session_object
    
    def get(self,session_id):
        """Return the session object using self.session_id, or an empty
        SessionElement instance"""
        return self.sessions.get(session_id,SessionElement(False))

class FileSessionStorage:

    # lock for thread-safe session storage
    rlock = threading.RLock()

    def __init__(self,session_dir):
        self.session_dir = session_dir
        if not os.path.exists(self.session_dir):
            try:
                os.mkdir(self.session_dir)
            except IOError:
                msg = "Can't create directory for file session storage %s"
                raise ValueError(msg %self.session_dir)

    def save(self,handler):
        """Save session object as a dictionary"""
        if hasattr(handler,'session_object'):
            self.rlock.acquire() # thread safety
            try:
                session_file = os.path.join(self.session_dir,handler.session_id)
                out = open(session_file,'wb')
                pickle.dump(dict(handler.session_object),out)
                out.close()
            except:
                traceback.print_exc(file=handler.output)
            self.rlock.release()
    
    def get(self,session_id):
        """Return the session object using self.session_id, or an empty
        SessionElement instance"""
        session_file = os.path.join(self.session_dir,session_id)
        try:
            try:
                self.rlock.acquire()
                obj = SessionElement(pickle.load(open(session_file,'rb')))
            except (IOError,AttributeError):
                obj = SessionElement()
                out = open(session_file,'wb')
                pickle.dump({},out)
                out.close()
        finally:
            self.rlock.release()
        return obj

class SQLiteSessionStorage:

    max_sessions = 100

    def __init__(self,path):
        self.path = path
        if self.path is None:
            raise ValueError("Path for SQLite session storage not defined")
        if not os.path.exists(self.path):
            try:
                conn = sqlite3.connect(self.path)
            except:
                msg = "Can't create a SQLite database with path %s"
                raise ValueError(msg %self.path)
            cursor = conn.cursor()
            fields = "session_id TEXT,mtime TEXT,s_obj TEXT"
            cursor.execute('CREATE TABLE sessions (%s)' %fields)

    def save(self,handler):
        """Save session object as a dictionary"""
        if hasattr(handler,'session_object'):
            try:
                obj = pickle.dumps(dict(handler.session_object))
                conn = sqlite3.connect(self.path)
                cursor = conn.cursor()
                cursor.execute('SELECT rowid FROM sessions WHERE session_id=?',
                    (handler.session_id,))
                res = cursor.fetchone()
                if not res:
                    sql = 'INSERT INTO sessions VALUES (?,?,?)'
                    now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                    cursor.execute(sql,(handler.session_id,now,obj))
                else:
                    rowid = res[0]
                    sql = 'UPDATE sessions SET mtime=?,s_obj=? WHERE rowid=?'
                    now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                    cursor.execute(sql,(now,obj,rowid))
                conn.commit()
                self.clear_sessions(conn)
            except:
                traceback.print_exc(file=handler.output)
    
    def get(self,session_id):
        """Return the session object using self.session_id, or an empty
        SessionElement instance"""
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sessions WHERE session_id=?',
            (session_id,))
        res = cursor.fetchone()
        if not res:
            obj = SessionElement()
            s_obj = pickle.dumps({})
            now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            cursor.execute('INSERT INTO sessions VALUEs (?,?,?)',
                (session_id,now,s_obj))
        else:
            obj = pickle.loads(res[2])
        return obj

    def clear_sessions(self,conn):
        # count nb of sessions
        cursor = conn.cursor()
        cursor.execute("SELECT mtime,rowid FROM sessions")
        res = cursor.fetchall()
        nb_sessions = len(res)
        if nb_sessions > 1.1*self.max_sessions:
            res.sort()
            # remove oldest sessions
            sql = "DELETE FROM sessions WHERE rowid=?"
            rowids = [ (x[1],) for x in res[:-self.max_sessions]]
            cursor.executemany(sql,rowids)
            conn.commit()
            cursor.execute("SELECT rowid FROM sessions")
