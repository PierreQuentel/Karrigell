Login("admin")
_ = Import('../translation.py').translate
banner = Import('banner.py')

def index():
    head = HEAD()
    head <= TITLE('Karrigell - '+_('Administration tools'))
    head <= LINK(rel="stylesheet",href="../style.css")
    container = DIV(Id="container")
    container <= banner.banner(home=True,title=_('Administration tools'))
    menu = DIV(Id="content")
    menu <= A(_('Users management'),href="../users.py")
    container <= menu
    return HTML(head+BODY(container))   

def logout():
    Logout()
    