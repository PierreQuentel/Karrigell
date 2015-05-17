import Karrigell
import Karrigell.admin_db

class App(Karrigell.App):
    root_dir = r'c:\Karrigell-Python3\tests'
    users_db = Karrigell.admin_db.SQLiteUsersDb(r'c:\Karrigell-Python3\admin_tools\users.sqlite')
    login_url = '/admin/login.py/login'

class App1(Karrigell.App):
    root_url = 'foo'
    users_db = Karrigell.admin_db.SQLiteUsersDb(r'c:\Karrigell-Python3\admin_tools\users1.sqlite')

apps = [App(),App1()]
