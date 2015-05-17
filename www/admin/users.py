Login(role="admin")

import Karrigell.admin_db
_ = Import('../translation.py').translate
banner = Import('banner.py')
levels = list(Karrigell.admin_db.levels.keys())

style = LINK(rel="stylesheet",href="../style.css")
head = TITLE(_("Users management"))+style

def index():
    body = DIV(Id="container")
    body <= banner.banner(home=True,title=_("Users management"))
    content = DIV(Id="content")
    content <= H2(_('Users management'))
    conn = THIS.users_db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT rowid,login,role,created,last_visit,nb_visits \
        FROM users')
    table = TABLE(Id="users-table")
    table <= TR(TH(_('login'))+TH(_('Role'))+TH(_('Created'))+
        TH(_('Last visit'))+TH(_('Visits')))
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        rowid,login,role,created,last_visit,nb_visits = row
        line = TD(A(login,href='edit?rowid={}'.format(rowid),Class="login"))
        line += TD(role)+TD(created)+TD(last_visit)+TD(nb_visits)
        
        table <= TR(line)

    form = FORM(action="new_entry")
    form <= INPUT(Type="submit",value=_("Insert new..."))
    
    content <= table + form
    body <= content
    return HTML(HEAD(head)+BODY(body))

def edit(rowid):
    body = DIV(Id="container")
    body <= banner.banner(home=True,title=_("Users management"))

    content = DIV(Id="content")
    content <= H4(_("Edit user information"))
    conn = THIS.users_db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT login,role FROM users WHERE rowid=?',(rowid,))
    login,role = cursor.fetchone()

    form = FORM(action="update",method="post")
    form <= DIV(_('login'),Class="login_prompt")
    form <= INPUT(name='login',value=login)
    form <= DIV(_('password')+'&nbsp;'+SMALL(_('(leave empty to keep the same)')),
        Class="login_prompt")
    form <= INPUT(Type="password",name="password",value='')
    form <= DIV(_('role'),Class="login_prompt")
    form <= SELECT(name="role").from_list(levels).select(content=role)
    form <= P()
    form <= INPUT(Type="hidden",name="rowid",value=rowid)
    form <= INPUT(Type="submit",name="b_update",value=_("update"))
    form <= INPUT(Type="submit",name="b_delete",value=_("delete"))
    form <= INPUT(Type="submit",name="b_cancel",value=_("cancel"))
    content <= form
    body <= content

    return HTML(HEAD(TITLE(_("Users management"))+style)+BODY(body))

def new_entry():
    body = DIV(Id="container")
    body <= banner.banner(home=True,title=_("Users management"))

    content = DIV(Id="content")
    content <= H4(_("New user"))
    form = FORM(action="insert",method="POST")
    form <= DIV(_('login'),Class="login_prompt")
    form <= INPUT(name='login',value='')
    form <= DIV(_('password'),Class="login_prompt")
    form <= INPUT(Type="password",name="password",value='')
    form <= DIV(_('role'),Class="login_prompt")
    form <= SELECT(name="role").from_list(levels).select(content=levels[-1])
    form <= P()+INPUT(Type="submit",value=_("insert"))
    content <= form
    body <= content
    return HTML(HEAD(head)+BODY(body))

def update(rowid,role,login='',password='',**kw):
    action = list(kw.keys())[0][2:]
    if login=='':
        return _error('Login field was empty')
    if len(login)<6:
        return _error('Login must be at least 6 character long')
    if password and len(password)<6:
        return _error('Password must be at least 6 character long')
    if login == password:
        return _error('Password and Login must be different')    
    role = levels[int(role)]
    if action == 'cancel':
        raise HTTP_REDIRECTION("index")
    conn = THIS.users_db.get_connection()
    cursor = conn.cursor()
    if action == 'update':
        if password:
            import hashlib
            _hash = hashlib.md5()
            _hash.update(password.encode('utf-8'))
            cursor.execute("UPDATE users SET login=?,role=?,password=? "
                "WHERE rowid=?",(login,role,_hash.digest(),rowid))
        else:
            cursor.execute("UPDATE users SET login=?,role=? WHERE rowid=?",
                (login,role,rowid))
        
    elif action == 'delete':
        cursor.execute("DELETE FROM users WHERE rowid=?",(rowid,))
    conn.commit()
    raise HTTP_REDIRECTION("index")

def _error(msg):
    body = DIV(Id="container")
    body <= banner.banner(home=True,title=_("Users management"))
    body <= DIV(msg,Id="content")
    return HTML(HEAD(head)+BODY(body))

def insert(**kw):
    if not 'login' in kw:
        return _error('Login field was empty')
    if not 'password' in kw:
        return _error('Login field was empty')
    login,password,role = kw['login'],kw['password'],int(kw['role'])
    if len(login)<6:
        return _error('Login must be at least 6 character long')
    if len(password)<6:
        return _error('Password must be at least 6 character long')
    if login == password:
        return _error('Password and Login must be different')    
    role = levels[int(role)]
    conn = THIS.users_db.get_connection()
    cursor = conn.cursor()
    try:
        THIS.users_db.add_user(login,password,role)
        raise HTTP_REDIRECTION("index")
    except ValueError as msg:
        body = DIV(Id="container")
        body <= banner.banner(home=True,title=_("Users management"))
        content = H2(_('Users management'))
        content += msg
        body <= content
        return HTML(HEAD(head)+BODY(body))
    