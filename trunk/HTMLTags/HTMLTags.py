# -*- coding: iso-8859-1 -*-

"""Classes to generate HTML in Python

The HTMLTags module defines a class for all the valid HTML tags, written in
uppercase letters. To create a piece of HTML, the general syntax is :
    t = TAG(content, key1=val1,key2=val2,...)

so that "print t" results in :
    <TAG key1="val1" key2="val2" ...>content</TAG>

For instance :
    print A('bar', href="foo") ==> <A href="foo">bar</A>

To generate HTML attributes without value, give them the value True :
    print OPTION('foo',SELECTED=True,value=5) ==> 
            <OPTION value="5" SELECTED>

The content argument can be an instance of an HTML class, so that 
you can nest tags, like this :
    print B(I('foo')) ==> <B><I>foo</I></B>

TAG instances support addition :
    print B('bar')+INPUT(name="bar") ==> <B>bar</B><INPUT name="bar">

and repetition :
    print TH('&nbsp')*3 ==> <TD>&nbsp;</TD><TD>&nbsp;</TD><TD>&nbsp;</TD>

For complex expressions, a tag can be nested in another using the operator <= 
Considering the HTML document as a tree, this means "add child" :

    form = FORM(action="foo")
    form <= INPUT(name="bar")
    form <= INPUT(Type="submit",value="Ok")

If you have a list (or any iterable) of instances, you can't concatenate the 
items with sum(instance_list) because sum takes only numbers as arguments. So 
there is a function called Sum() which will do the same :

    Sum( TR(TD(i)+TD(i*i)) for i in range(100) )

generates the rows of a table showing the squares of integers from 0 to 99

A simple document can be produced by :
    print HTML( HEAD(TITLE('Test document')) +
        BODY(H1('This is a test document')+
             'First line'+BR()+'Second line'))

If the document is more complex it is more readable to create the elements 
first, then to print the whole result in one instruction. For example :

===================
head = HEAD()
head <= TITLE('Record collection')
head <= LINK(rel="Stylesheet",href="doc.css")

title = H1('My record collection')
table = TABLE()
table <= TR(TH('Title')+TH('Artist'))
for rec in records:
    row = TR()
    # note the attribute key Class with leading uppercase 
    # because "class" is a Python keyword
    row <= TD(rec.title,Class="title")+TD(rec.artist,Class="artist")
    table <= row

print HTML(head+BODY(title+table))
==================

Content or attribute value are (Unicode) strings. The __str__() method also
returns a string
"""
import sys
import io

class TAG:
    """Generic class for tags"""
    def __init__(self, *content, **attrs):
        self.tag = self.__class__.__name__
        self.attrs = attrs
        # we can't init with argument content='' because of conflict
        # if a key 'content' is in **attrs
        if not content:
            self.children = []
        elif len(content)>1:
            raise ValueError('%s takes only one positional argument' %self.tag)
        elif isinstance(content[0],TAG) and content[0].__class__ is TAG: 
            # abstract class with no parent
            self.children = content[0].children
        else:
            self.children = [content[0]]
        self._update_parent()

    def _update_parent(self):
        for child in self.children:
            if isinstance(child,TAG):
                child.parent = self

    def __str__(self):
        res=io.StringIO()
        w=res.write
        if self.tag == "COMMENT":
            w("<!--")
            for child in self.children:
                w(str(child))
            w("-->")
            return res.getvalue()
        elif self.tag not in ["TAG"]:
            w("<%s" %self.tag.lower())
            # attributes which will produce arg = "val"
            attr1 = [ k for k in self.attrs 
                if not isinstance(self.attrs[k],bool) ]
            attr_list = []
            for k in attr1:
                key = k.replace('_','-')
                value = self.attrs[k]
                attr_list.append(' %s="%s"' %(key,value))
            w("".join(attr_list))
            # attributes with no argument
            # if value is False, don't generate anything
            attr2 = [ k for k in self.attrs if self.attrs[k] is True ]
            w("".join([' %s' %k for k in attr2]))
            w(">")
        if self.tag in _ONE_LINE:
            w('\n')
        for child in self.children:
            w(str(child))
        if self.tag in _CLOSING_TAGS:
            w("</%s>" %self.tag.lower())
        if self.tag in _LINE_BREAK_AFTER:
            w('\n')
        return res.getvalue()

    def show(self,indent=0,attrs=False):
        res = ' '*indent+self.tag
        if attrs:
            res += str(self.attrs)
        res += '\n'
        for child in self.children:
            if isinstance(child,TAG):
                res += child.show(indent+1,attrs)
        return res
    
    def __le__(self,other):
        """Add a child"""
        if other.__class__ is TAG:
            self.children += other.children
        else:
            self.children.append(other)
        self._update_parent()
        return self

    def __add__(self,other):
        """Return a new instance : concatenation of self and another tag"""
        if self.__class__ is TAG:
            if other.__class__ is TAG:
                self.children += other.children
            else:
                self.children.append(other)
            self._update_parent()
            return self
        else:
            res = TAG() # abstract tag
            res.children = [self,other]
            res._update_parent()
            return res

    def __radd__(self,other):
        """Used to add a tag to a string"""
        if isinstance(other,str):
            return TEXT(other)+self
        else:
            raise ValueError("Can't concatenate %s and instance" %other)

    def __mul__(self,n):
        """Replicate self n times, with tag first : TAG * n"""
        res = TAG()
        res.children = [self for i in range(n)]
        return res

    def __rmul__(self,n):
        """Replicate self n times, with n first : n * TAG"""
        return self*n

    def __contains__(self,attr):
        return attr in self.attrs

    def __getitem__(self,attr):
        return self.attrs[attr]
    
    def __setitem__(self,key,value):
        self.attrs[key] = value

    def get_by_attr(self,**kw):
        """Return a list of tags whose attributes are in kw,
        at the same level as self or below in the tree"""
        res = []
        flag = True
        for k,v in kw.items():
            if not k in self.attrs or not self.attrs[k] == v:
                flag = False
                break
        if flag:
            res.append(self)
        for child in self.children:
            if isinstance(child,TAG):
                res += child.get_by_attr(**kw)
        return _tag_list(res)

    def get_by_tag(self,tag_name):
        """Return a list of tags of specified tag name,
        at the same level as self or below in the tree"""
        res = []
        if self.tag == tag_name:
            res.append(self)
        for child in self.children:
            if isinstance(child,TAG):
                res += child.get_by_tag(tag_name)
        return _tag_list(res)

    def get(self,*tags,**kw):
        """Search instances of classes in tags with attributes = kw"""
        res = []
        if not tags or self.__class__ in tags:
            flag = True
            for (k,v) in kw.items():
                if k not in self.attrs or v != self.attrs[k]:
                    flag = False
            if flag:
                res.append(self)
        for child in self.children:
            if isinstance(child,TAG):
                res+= child.get(*tags,**kw)
        return res

    def delete(self,subtag):
        """Delete subtag"""
        subtag.parent.children.remove(subtag)
        
class _tag_list(list):

    def set_attr(self,**kw):
        for item in self:
            for key,value in kw.items():
                item.attrs[key] = value

# list of tags, from the HTML 4.01 specification

_CLOSING_TAGS =  ['A', 'ABBR', 'ACRONYM', 'ADDRESS', 'APPLET',
            'B', 'BDO', 'BIG', 'BLOCKQUOTE', 'BUTTON',
            'CAPTION', 'CENTER', 'CITE', 'CODE',
            'DEL', 'DFN', 'DIR', 'DIV', 'DL',
            'EM', 'FIELDSET', 'FONT', 'FORM', 'FRAMESET',
            'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
            'I', 'IFRAME', 'INS', 'KBD', 'LABEL', 'LEGEND',
            'MAP', 'MENU', 'NOFRAMES', 'NOSCRIPT', 'OBJECT',
            'OL', 'OPTGROUP', 'PRE', 'Q', 'S', 'SAMP',
            'SCRIPT', 'SMALL', 'SPAN', 'STRIKE',
            'STRONG', 'STYLE', 'SUB', 'SUP', 'TABLE',
            'TEXTAREA', 'TITLE', 'TT', 'U', 'UL',
            'VAR', 'BODY', 'COLGROUP', 'DD', 'DT', 'HEAD',
            'HTML', 'LI', 'P', 'TBODY','OPTION', 
            'TD', 'TFOOT', 'TH', 'THEAD', 'TR']

_NON_CLOSING_TAGS = ['AREA', 'BASE', 'BASEFONT', 'BR', 'COL', 'FRAME',
            'HR', 'IMG', 'INPUT', 'ISINDEX', 'LINK',
            'META', 'PARAM']

# new HTML5 tags
_CLOSING_TAGS += [ 'ARTICLE','ASIDE','FIGURE','FOOTER','HEADER','NAV',
    'SECTION','AUDIO','VIDEO','CANVAS','COMMAND','COMMENT','DATALIST',
    'DETAILS','OUTPUT','PROGRESS','HGROUP','MARK','METER','TIME',
    'RP','RT','RUBY']

_NON_CLOSING_TAGS += ['SOURCE']

# create the classes
for _tag in _CLOSING_TAGS + _NON_CLOSING_TAGS + ['TEXT']:
    exec("class %s(TAG): pass" %_tag)

# Convenience methods for SELECT tags, radio and checkbox INPUT tags

def _check_args(**kw):
    # check if arguments are valid for selection or check methods
    if not kw:
        raise ValueError('No arguments provided')
    elif len(kw.keys())>1:
        msg = 'Function takes 1 argument, %s provided'
        raise ValueError(msg %len(kw.keys()))
    elif list(kw.keys())[0] not in ['content','value']:
        msg ='Bad argument %s, must be "content" or "value"'
        raise ValueError(msg %kw.keys()[0])
    return list(kw.keys())[0],list(kw.values())[0]

# SELECT has special methods to build a list of OPTION tags from
# a list, and marks one of several OPTION tags as selected
_CLOSING_TAGS.append('SELECT')

class SELECT(TAG):

    def from_list(self,_list,use_content=False):
    # build a SELECT tag from a list
        if not use_content:
            # values are content's rank
            self.children = [OPTION(item,value=i,SELECTED=False) 
                for (i,item) in enumerate(_list)]
        else:
            # values are content's value
            self.children = [OPTION(item,value=item,SELECTED=False) 
                for item in _list]
        return self

    def select(self,**kw):
    # mark an option (or several options if attribute MULTIPLE is set) as selected
        key,attr = _check_args(**kw)
        if not isinstance(attr,(list,tuple)):
            attr = [attr]
        if key == 'content':
            for option in self.children:
                option.attrs['SELECTED'] = option.children[0] in attr
        elif key == 'value':
            for option in self.children:
                option.attrs['SELECTED'] = option.attrs['value'] in attr
        return self

# Classes to build a list of radio and checkbox INPUT tags from a list
# of strings. All INPUT tags have the same attributes, including name
# and except the value, which is the string index in the list

# Instances of RADIO and CHECKBOX have a check() method, used to mark
# INPUT tags as checked. The argument can be a string value (or a list
# of strings) to check the tags associated with one of the items in the
# list, or an index (or a list of indices)

class RADIO:

    def __init__(self,_list,_values=None,**attrs):
        self._list = _list
        if _values is None :
            self.tags = [INPUT(Type="radio",value=i,checked=False,**attrs)
                    for i in range(len(_list))]
        else:
            if not isinstance(_values, (list, tuple)) :
                raise TypeError("_values must be a list or a tuple")
            if len(_list) != len(_values) :
                raise ValueError("len(_list) != len(_values)")
            self.tags = [INPUT(Type="radio",value=i,checked=False,**attrs)
                    for i in _values]

    def check(self,**kw):
        key,attr = _check_args(**kw)
        if key == 'content':
            for i,item in enumerate(self._list):
                self.tags[i].attrs['checked'] = self._list[i] == attr
        else:
            for (i,tag) in enumerate(self.tags):
                self.tags[i].attrs['checked'] = tag.attrs['value'] == attr

    def __iter__(self):
        return iter(zip(self._list,self.tags))

class CHECKBOX:

    def __init__(self,_list,_values=None,**attrs):
        self._list = _list
        if _values is None :
            self.tags = [INPUT(Type="checkbox",value=i,checked=False,**attrs)
                    for i in range(len(_list))]
        else:
            if not isinstance(_values, (list, tuple)) :
                raise TypeError("_values must be a list or a tuple")
            if len(_list) != len(_values) :
                raise ValueError("len(_list) != len(_values)")
            self.tags = [INPUT(Type="checkbox",value=i,checked=False,**attrs)
                    for i in _values]

    def check(self,**kw):
        key,attr = _check_args(**kw)
        if not isinstance(attr,(tuple,list)):
            attr = [attr]
        if key == 'content':
            for i,item in enumerate(self._list):
                self.tags[i].attrs['checked'] = self._list[i] in attr
        else:
            for (i,tag) in enumerate(self.tags):
                self.tags[i].attrs['checked'] = tag.attrs['value'] in attr

    def __iter__(self):
        return iter(zip(self._list,self.tags))

def Sum(iterable):
    """Return the concatenation of the instances in the iterable
    Can't use the built-in sum() on non-integers"""
    it = [ item for item in iterable ]
    if it:
        res = it[0]
        for item in it[1:]:
            res += item
        return res
    else:
        return ''

# whitespace-insensitive tags, determines pretty-print rendering
_LINE_BREAK_AFTER = _NON_CLOSING_TAGS + ['HTML','HEAD','BODY',
    'FRAMESET','FRAME',
    'TITLE','SCRIPT',
    'TABLE','TR','TD','TH','SELECT','OPTION',
    'FORM',
    'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
    'UL','LI','OL','DIV','SPAN'
    ]
# tags whose opening tag should be alone in its line
_ONE_LINE = ['HTML','HEAD','BODY',
    'FRAMESET'
    'SCRIPT',
    'TABLE','TR','SELECT','OPTION',
    'FORM','UL','OL'
    ]

if __name__ == '__main__':
    head = HEAD(TITLE('Test document'))
    body = BODY()
    body <= H1('This is a test document')
    lines = 'First line' + BR() + 'Second line'+DIV(H1("zone"),name="zone")
    body <= lines

    print(lines.get_by_attr(name="zone"))
    print(body.get_by_attr(name="zone"))

    for tag in body.get_by_tag("H1"):
        print(tag)

    print(HTML(head + body))

    print(TD(B('d')+I('a'))*3)
    
    formats = ['DEFAULT','DATE (YYYY-MM-DD)',
        'TIME (HH:MM:SS)','TIMESTAMP (YYY-MM-DD HH:MM:SS)']
    sf = SELECT().from_list(formats)
    sf.select(content='TIME (HH:MM:SS)')
    print(sf)
    
    s = SELECT(name="foo",MULTIPLE=True).from_list(['a','b','c','e'])
    s.select(content=['b','d'])
    print(s)
    
    lines = TR(TD("Login�")+TD(INPUT(name="login")))
    lines += TR(TD("Password")+TD(INPUT(name="passwd",Type="passwordî")))
    lines += TR(TD(INPUT(Type="submit",value="Ok"),colspan="2",align="center"))
    print(len(lines.get_by_tag('TD')),"TD tags in line")

    lines.get_by_tag('TD').set_attr(Class="menu")
    print(lines)
    
    print("à"+B('z'))

    print(COMMENT('commentaire'))