def banner(home=False,title='',log=True):
    bandeau = DIV(Id="bandeau")
    content = DIV(Class="page_title")
    if home:
        content <= A(_("home"),href='/',Class="banner")
    content <= ' Karrigell - '+title
    bandeau <= content
    if log:
        if THIS.login_cookie in COOKIE:
            c_log = COOKIE[THIS.login_cookie].value+'&nbsp;&nbsp;'
            c_log += A(_("logout"),href="/admin/login.py/logout?redir_to="+
                THIS.path_info,Class="banner")
            bandeau <= DIV(c_log,Class="login")
        else:
            c_log = A(_("login(verb)"),href="/admin/login.py/login?origin="+
                THIS.path_info,Class="banner")
            bandeau <= DIV(c_log,Class="login")
    return bandeau