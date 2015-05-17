_ = Import('translation.py').translate
banner = Import('admin/banner.py')

def index():
    head = LINK(rel="stylesheet",href="/admin/style.css")
    head += TITLE('Karrigell home page')
    container = DIV(Id="container")
    container <= banner.banner(title = _("home"))
    content = DIV(Id="content")
    content <= _("installed")
    content <= P()+A("Administration",href="/admin/index.py")
    content <= P()+A("Documentation",href="/doc/Home.html")
    container <= content
    return HTML(HEAD(head)+BODY(container))