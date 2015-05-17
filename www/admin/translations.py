Login("admin")

import os
import html
import urllib.parse

banner = Import('banner.py')
script_strings = Import("script_strings.py")
lang_list = Import("langs.py")

head = HEAD(
    LINK(rel="stylesheet",href="../style.css")+
    META(http_equiv="Content-Type",content="text/html; charset=utf-8")
    )

def index(url_path='/'):
    # url path is unquoted
    head <= TITLE('Karrigell - '+_('Administration tools'))
    container = DIV(Id="container")
    container <= banner.banner(home=True,title=_('Translations'))
    
    if THIS.translation_db is None:
        content = DIV(style="padding:50px;")
        content <= H3("No translation database set")
        container <= content
        return HTML(head+BODY(container))

    strings = set()
    for _strings in get_strings().values():
        strings.update(set(_strings))

    for src in strings:
        if not THIS.translation_db.get_original(src):
           THIS.translation_db.insert_original(src)

    elts = url_path.lstrip('/').split('/')

    links = A("..",href="?")+' / '
    for (i,elt) in enumerate(elts[:-1]):
        address = '/'.join(elts[:i+1])
        address = urllib.parse.quote_plus(address)
        links += A(elt or '..',href="index?url_path=/"+address)+ '/ '
    links += B(elts[-1])            
    container <= links

    table = TABLE(Id="navig")
    fs_path = THIS.get_file(url_path)
    if os.path.isdir(fs_path):
        folder = fs_path
        url_path = url_path.rstrip('/')+'/'
    else:
        folder = os.path.dirname(fs_path)
    paths = os.listdir(folder)
    subfolders = [ p for p in paths if os.path.isdir(os.path.join(folder,p)) ]
    for subfolder in subfolders:
        sub_url = urllib.parse.urljoin(url_path,subfolder)
        href="?url_path="+urllib.parse.quote_plus(sub_url)
        row = TR()
        row <= TD(A(IMG(src="../folder_open.png",border=0),href=href))
        row <= TD(A(subfolder,href=href,Class="subfolder"))
        table <= row

    has_encoding_errors = set()

    files = [ p for p in paths if os.path.isfile(os.path.join(folder,p)) ]
    for _file in files:
        abs_path = os.path.join(folder,_file)
        if os.path.splitext(_file)[1] == '.py':
            try:
                strings = script_strings.get_strings(abs_path)
                if strings:
                    sub_path = urllib.parse.urljoin(url_path,_file)
                    sub_path = urllib.parse.quote_plus(sub_path)
                    cell = A(_file,href="?url_path={}".format(sub_path),
                        Class="localize")
                else:
                    cell = _file
            except UnicodeDecodeError:
                cell = _file+"*"
                has_encoding_errors.add('py')
        elif os.path.splitext(_file)[1] == '.kt':
            try:
                strings = script_strings.get_strings_kt(abs_path)
                if strings:
                    sub_path = urllib.parse.urljoin(url_path,_file)
                    sub_path = urllib.parse.quote_plus(sub_path)
                    cell = A(_file,href="?url_path={}".format(sub_path),
                        Class="localize")
                else:
                    cell = _file
            except UnicodeDecodeError:
                cell = _file+"*"
                has_encoding_errors.add('kt')
        else:
            cell = _file
        table <= TR(TD('&nbsp;')+TD(cell))

    content = TABLE()
    row = TR()
    row <= TD(table,valign="top")

    if os.path.isfile(fs_path):
        row <= TD(_translator(url_path,fs_path),Class="translation")
    elif has_encoding_errors:
        msg = encoding_warning
        if "py" in has_encoding_errors:
            msg += P()+encoding_warning_py
        if "kt" in has_encoding_errors:
            msg += P()+encoding_warning_kt
        row <= TD(msg,Class="warning",valign="top")
    content <= row
    container <= content
    return HTML(head+BODY(container))

encoding_warning = """The files marked with * have encoding errors :
either they have no encoding declared, or the encoding declared can't be used
to decode the file"""
encoding_warning_py = """For Python scripts, the encoding is defined by
a line such as <br># -*- coding: <B>utf-8</B> -*-<br>"""
encoding_warning_kt = """For Karrigell Template (KT) the encoding is defined
in a META tag such as <P><SPAN style="font-family:Courier">
&lt;META http-equiv="Content-type" 
content="text/html;charset=<B>utf-8</B>"&gt;
</SPAN>"""

wrong_encoding_error = _("""The encoding defined in the META tag, {encoding}, 
can't be used to decode its content""")

missing_encoding_error = _("""
No encoding is defined. The default encoding, {encoding}, can't be used to 
decode its content.<br>
Add a META tag such as :<P>
<SPAN style="font-family:Courier">
&lt;META http-equiv="Content-type" 
content="text/html;charset=<B>{other_encoding}</B>"&gt;
</SPAN>
<P>where you replace <B>{other_encoding}</B> by the appropriate encoding""")

def _translator(url_path,script):
    name = os.path.basename(script)
    ext = os.path.splitext(script)[1]
    if ext == ".py":
        strings = script_strings.get_strings(script)
    elif ext == ".kt":
        try:
            strings = script_strings.get_strings_kt(script)
        except UnicodeDecodeError:
            msg = "Unicode error in template {}".format(script)+P()
            encoding = script_strings.guess_encoding(script)
            if encoding:
                return msg + wrong_encoding_error.format(encoding=encoding)
            else:
                other_encoding = 'utf-8'
                if ENCODING == other_encoding:
                    other_encoding = 'iso-8859-1'
                return msg + missing_encoding_error.format(encoding=ENCODING,
                    other_encoding=other_encoding)
    langs = ACCEPTED_LANGUAGES
    if not langs:
        return _("You must select the language in your browser")
    # select prefered language form browser preferences
    lang = langs.split(",")[0].split(";")[0][:2]

    header = TR()
    header <= TH(_("Original string in script"))
    lang_str = lang
    if lang in lang_list.langs:
        lang_str += ' ({})'.format(lang_list.langs[lang])
    header <= TH(_('Translation into')+'&nbsp;'+lang_str)
    lines = [header]
    for i,_string in enumerate(strings):
        rowid = THIS.translation_db.get_original(_string)
        line = TD(_string)+INPUT(Type="hidden",name="orig-%s" %i,value=rowid)
        _trans = THIS.translation_db.get_translation(_string,lang)
        if _trans is None:
            _string1 = html.escape(_string,quote=True)
            _input = TEXTAREA(_string1,name="%s-%s" %(lang,i),
                    cols=35,rows=1+len(_string1)/25,
                    style="font-style:italic;")
        else:
            _trans = html.escape(_trans,quote=True)
            _input = TEXTAREA(_trans,name="%s-%s" %(lang,i),
                    cols=35,rows=1+len(_trans)/25)
        line += TD(_input)
        lines += [TR(line)]
    
    explain = I(_('Strings in italic have no translation yet. '))+BR()
    explain += _('To change the language, update your browser languages list')
    
    form = FORM(action="update",method="post")
    form <= TABLE(Sum(lines),Id="hor-minimalist-b")
    form <= INPUT(Type="hidden",name="url_path",value=url_path)
    form <= INPUT(Type="submit",value=_("Save translations"))
    
    return explain+form

def update(**kw):
    url_path = kw['url_path']
    del kw['url_path']
    dico = {}
    for k,v in kw.items():
        lang,num = k.split("-")
        if not num in dico:
            dico[num]={lang:v}
        else:
            dico[num][lang] = v

    for num in dico:
        orig_id = dico[num]['orig']
        for language in [ lang for lang in dico[num] if lang != 'orig' ]:
            THIS.translation_db.set_translation(orig_id,language,
                dico[num][language])
    raise HTTP_REDIRECTION("index?url_path="+url_path)

def test():
    body = H2('Translation database')
    t = TABLE(border=1)
    conn = THIS.translation_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT rowid,original FROM translation_original")
    for (rowid,original) in cursor.fetchall():
        original = html.escape(original,quote=True)
        cursor.execute("SELECT language,translated FROM translation \
            WHERE orig_id=?",(rowid,))
        for (language,translated) in cursor.fetchall():
            t <= TR(TD('[%s]'%len(original)+PRE(original))+TD(language)+TD(PRE(translated)))
    return body+t

def get_strings():
    strings = {}
    errors = []
    for dirpath,dirnames,filenames in os.walk(THIS.root_dir):
        for _file in filenames:
            abs_path = os.path.join(dirpath,_file)
            if os.path.splitext(_file)[1] == '.py':
                try:
                    strings[abs_path] = script_strings.get_strings(abs_path)
                except UnicodeDecodeError:
                    errors.append(abs_path)
            elif os.path.splitext(_file)[1] == '.kt':
                try:
                    strings[abs_path] = script_strings.get_strings_kt(abs_path)
                except UnicodeDecodeError:
                    errors.append(abs_path)
    return strings
            