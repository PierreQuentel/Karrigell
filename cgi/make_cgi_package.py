# Generates files to run Karrigell on CGI mode with the Apache web server
# Based on the configuration file cgi.ini

import os
import shutil
import datetime
import configparser

import Karrigell

name = 'Karrigell-{}-cgi'.format(Karrigell.version)

parent = os.path.dirname(os.getcwd())

dest_dir = os.path.join(os.getcwd(),'cgi-package')
if os.path.exists(dest_dir):
    shutil.rmtree(dest_dir)
os.mkdir(dest_dir)
local_cgi_dir = os.path.join(dest_dir,'cgi-bin')
os.mkdir(local_cgi_dir)
local_root_dir = os.path.join(dest_dir,'root_directory')
os.mkdir(local_root_dir)

config = configparser.ConfigParser()
config.read('cgi.ini')
config = config['CONFIG']

python_path = config['python_path']
root_url = config['root_url']
root_dir = config['root_dir']
users_db_path = config['users_db_path']

out = open(os.path.join(local_cgi_dir,'cgi_config.py'),'w')
out.write("# generated ")
out.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S\n"))
out.write("""import Karrigell
import Karrigell.admin_db

class App(Karrigell.App):
    root_url = '{}'
    root_dir = r'{}'""".format(root_url,root_dir))

if users_db_path:
    out.write("\n    users_db = Karrigell.admin_db.SQLiteUsersDb(r'{}')".format(
        users_db_path))
    login_url = root_url.rstrip('/')+'/admin/login.py/login'
    out.write("\n    login_url = '{}'".format(login_url))

out.write('\n\napps = [App()]\n')
out.close()

cgi_url = config['cgi_url']

htaccess = """
# this is the .htaccess file for CGI mode
Options -Indexes -MultiViews

ErrorDocument 403 {0}/k_handler.cgi

# rewrite urls so that Karrigell handles all scripts
# excecpt those with static files extension

RewriteEngine On
RewriteCond  %{{SCRIPT_FILENAME}} !\.cgi$
RewriteCond  %{{SCRIPT_FILENAME}} !\.(html|htm|css|js|jpg|jpeg|gif|png)$

RewriteRule (.*) {0}/k_handler.cgi
"""

out = open(os.path.join(local_root_dir,'.htaccess'),'w')
out.write(htaccess.format(cgi_url))
out.close()
print('add','.htaccess')

# default folder www
www_path = os.path.join(parent,'www')
for path in ['index.py','translation.py','translations.ini']:
    print('add',path)
    shutil.copyfile(os.path.join(www_path,path),
        os.path.join(local_root_dir,path))

# if users db defined, add folder admin
if users_db_path:
    os.mkdir(os.path.join(local_root_dir,'admin'))
    admin_path = os.path.join(parent,'www','admin')
    for filename in os.listdir(admin_path):
        if filename.startswith('.'):
            continue
        print('add',filename)
        shutil.copyfile(os.path.join(admin_path,filename),
            os.path.join(local_root_dir,'admin',filename))

# replace first line of k_handler with the right Python path
lines = open('k_handler.cgi').readlines()
lines[0] = '#!'+python_path+'\n'
out = open(os.path.join(local_cgi_dir,'k_handler.cgi'),'w')
out.writelines(lines)
out.close()

# add Karrigell and HTMLTags modules
for path in ['Karrigell','HTMLTags']:
    abs_path = os.path.join(parent,path)
    os.mkdir(os.path.join(local_cgi_dir,path))
    for filename in os.listdir(abs_path):
        src = os.path.join(abs_path,filename)
        if os.path.isfile(src):
            print('add',filename)
            shutil.copyfile(src,os.path.join(local_cgi_dir,path,filename))

method = config['method']
if method == "copy":
    # copy root directory
    for path in os.listdir(local_root_dir):
        src = os.path.join(local_root_dir,path)
        if os.path.isfile(src):
            dest = os.path.join(root_dir,path)
            shutil.copyfile(src,dest)
            print('copy',path)
    local_admin_dir = os.path.join(local_root_dir,'admin')
    admin_dir = os.path.join(root_dir,'admin')
    if not os.path.exists(admin_dir):
        os.mkdir(admin_dir)
    for path in os.listdir(local_admin_dir):
        src = os.path.join(local_admin_dir,path)
        if os.path.isfile(src):
            dest = os.path.join(admin_dir,path)
            shutil.copyfile(src,dest)
            print('copy',path)
    # copy cgi directory
    cgi_dir = config['cgi_dir']
    for path in os.listdir(local_cgi_dir):
        src = os.path.join(local_cgi_dir,path)
        if os.path.isfile(src):
            dest = os.path.join(cgi_dir,path)
            shutil.copyfile(src,dest)
            print('copy',path)    

print("""
The Karrigell distribution for CGI was created successfully in subfolder
cgi-package
Copy/upload the content of subfolder "cgi_bin" in the CGI directory 
and the content of subfolder "root_directory" in the root directory. Then 
enter http://<hostname>/<root-url> in a browser. You should see the message
"Karrigell successfully installed" """)
