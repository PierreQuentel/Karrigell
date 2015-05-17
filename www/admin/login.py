import datetime
_ = Import('../translation.py').translate
banner = Import('banner.py')

lifetime = 30 # how long a cookie lasts, in days

style = LINK(rel="stylesheet",href="../style.css")

def login(origin,role=None):
    container = DIV(Id="container")
    container <= banner.banner(home=True,title=_("login(verb)"),log=False)
    
    if THIS.users_db is None:
        container <= 'No users database declared for this application'
    elif THIS.users_db.is_empty():
        container <= H4(_("empty_db"))
        form_container = DIV(Id="form_container")
        form = FORM(action="set_admin",method="POST")
        form <= INPUT(Type="hidden",name="origin",value=origin)
        form <= DIV(_('login'),Class="login_prompt")
        form <= INPUT(name='login')
        form <= DIV(_('password'),Class="login_prompt")
        form <= INPUT(Type="password",name="password")
        form <= P()+INPUT(Type="submit",value="Ok")
        form_container <= form
        container <= form_container
    else:
        role = role or "-1"
        form_container = DIV(Id="form_container")
        form = FORM(action="check_login",method="POST")
        form <= INPUT(Type="hidden",name="origin",value=origin)
        form <= INPUT(Type="hidden",name="required_role",value=role)
        form <= DIV(_('login'),Class="login_prompt")
        form <= INPUT(name='login')
        form <= DIV(_('password'),Class="login_prompt")
        form <= INPUT(Type="password",name="password")
        save = DIV(Class="remember_prompt")
        save <= _('remember me')
        save <= INPUT(Type="checkbox",name="remember")
        form <= save
        form <= P()+INPUT(Type="submit",value="Ok")
        form_container <= form
        container <= form_container

    return HTML(HEAD(TITLE('Login')+style)+BODY(container))

def _set_cookies(remember,login,password):
    SET_COOKIE[THIS.login_cookie] = login
    SET_COOKIE[THIS.login_cookie]['path'] = THIS.root_url
    if remember: # persistent cookie
        import datetime
        new = datetime.date.today() + datetime.timedelta(days = lifetime) 
        SET_COOKIE[THIS.login_cookie]['expires'] = new.strftime("%a, %d-%b-%Y 23:59:59 GMT")
        SET_COOKIE[THIS.login_cookie]['max-age'] = lifetime*24*3600 # seconds

    import random
    import string
    skey = ''.join(random.choice(list(string.ascii_letters+string.digits))
        for i in range(16))
    THIS.users_db.set_session_key(login,skey)
    SET_COOKIE[THIS.skey_cookie] = skey
    SET_COOKIE[THIS.skey_cookie]['path'] = THIS.root_url
    if remember: # cookie will live 30 days
        SET_COOKIE[THIS.skey_cookie]['expires'] = \
            new.strftime("%a, %d-%b-%Y 23:59:59 GMT")
        SET_COOKIE[THIS.skey_cookie]['max-age'] = lifetime*24*3600 # seconds

def check_login(required_role,origin,login,password,remember=False):
    db = THIS.users_db
    if required_role == "-1":
        required_role = None
    if db.user_has_role(login,password,required_role):
        _set_cookies(remember,login,password)
        THIS.users_db.update_visits(SET_COOKIE[THIS.skey_cookie].value)
    raise HTTP_REDIRECTION(origin)

def set_admin(origin,login,password):
    if not THIS.users_db.is_empty():
        raise HTTP_ERROR(500,'db not empty')
    THIS.users_db.add_user(login,password,'admin')
    _set_cookies(False,login,password)
    raise HTTP_REDIRECTION(origin)

def logout(redir_to):
    Logout(redir_to)