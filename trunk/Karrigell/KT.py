"""KT -- Karrigell Template

Provides a means of performing substitutions and translations in templates
stored in separate files. Template files are referenced by URLs when KT is 
used within the Karrigell framework .Templates can include other templates.

Template syntax
===============
@[template_url]
  include template referenced by template_url]
    
_[string_to_translate]
  apply standard Karrigell string translation to string_to_translate
    
$identifier
  subtitute the value of identifier
  
$container.attribute
  substitute the value of container.attribute or container['attribute'] 
    
These combinations are also possible:

@[$template_url]
_[$string]

Initialisation within a Karrigell script
========================================
KT is included as a keyword within Karrigell. Use it like this:

kt = KT()

kt can also be initialised with a default encoding and a translation
function:

ENCODING = 'utf-8'
_ = Import('translations.py').translate
kt = KT(translate=_, encoding=ENCODING)

Rendering a template
====================
There are a number of possible ways to pass data to a template:

1. Passing individual variables:
text = kt.render(templ_file, id1=val1, id2=val2, ...)

2. Passing a dictionary: 
text = kt.render(templ_url, **data)
  where data is a dictionary of values to substitute.

3. Passing dictionaries or objects by name:
text = kt.render(templ_file, data=locals(), this=THIS)
  Values/attributes of the passed object can be referenced 
  using dot notation in the templates:
  $data.var1   $this.root_dir

Encoding management
===================
The default encoding for the TemplateEngine instance can be specified on 
initialisation:

kt = KT(encoding='utf-8')

If a specific template is encoded with another encoding, you can specify it with :
text = kt.render(template_file, encoding=foo)

All the included urls in this template are also supposed to be encoded with
this encoding. If some of them are encoded with a different encoding their
encoding must be specified after the included template file name :
@[included_templ,encoding]

Use of KT as a stand-alone template engine
==========================================
KT can also be used as a stand-alone template engine. When used outside of the
Karrigell framework, file system paths are used instead of URLs to give the 
locations of the templates. 

from Karrigell.KT import KT
kt = KT(encoding='utf-8')
var1 = 'value 1'
var2 = 'value 2'
print(kt.render('master.kt', data=locals())

For convenience, a template directory can be specified on initialisation. e.g.

from Karrigell.KT import KT
kt = KT(templ_dir='/myapp/templates', encoding='utf-8')
var1 = 'value 1'
var2 = 'value 2'
print(kt.render('master.kt', data=locals())

In this case 'master.kt' is joined to '/myapp/templates' using os.path.join to 
give the full path to the template file.
"""

import sys, os
import urllib.parse
import re

class RecursionError(Exception):
    pass

class NotFoundError(Exception):
    pass

class KTError(Exception):
    pass

"""
def _log(*data):
    import sys
    for item in data:
        sys.stderr.write('%s\n' %item)
"""

class KT:
    def __init__(self, templ_dir='',
                encoding='utf-8',
                translate=str,
                handler=None
                ):
        self.translation_func = translate
        self.encoding = encoding
        self.templ_dir = templ_dir
        self.handler = handler
        self.included_paths = []
    
    def __call__(self,template,encoding='utf-8',**namespace):
        return self.render(template,encoding='utf-8',**namespace)
        
    def render(self,template,encoding=None,**namespace):
        if not encoding:
            encoding = self.encoding
        # If handler is defined then we are running within the 
        # Karrigell framework. Convert URLs to absolute fs paths
        if self.handler:
            abs_url = self.handler.abs_url(template)
            templ_path = self.handler.get_file(abs_url)
        else:
            templ_path = os.path.join(self.templ_dir,template)
        if not os.path.isfile(templ_path):
            raise NotFoundError('No template file at path %s' %templ_path)
        with open(templ_path,encoding=encoding,errors='replace') as fileobj:
            templ = fileobj.read()               
        self.included_paths.append(templ_path)
        result = self._include(templ, namespace, templ_path)
        result = self._substitute(result, namespace)
        if self.translation_func:
            result = self._translate(result)
        return result

    def _include(self, text, namespace, parent_path):
        regex = re.compile(r"""
            \@(?:
                (?P<escaped>\@)                     | # Escape sequence of two delimiters
                \[(?P<id>\$[_a-z][_a-z0-9\.]*)\]    | # a bracketed Python identifier
                \[(?P<path>.*?[^\\])\]              | # a bracketed url
                (?P<invalid>)                         # Other ill-formed delimiter exprs
            )
            """, re.IGNORECASE | re.VERBOSE)
        def helper(mo):
            path = None
            if mo.group('escaped') is not None:
                return mo.group(0)
            url = ''
            if mo.group('id') is not None:
                id = str(mo.group('id'))
                path = self._substitute(id, namespace)
                # if id has no value, don't attempt to open the url.
                if not path or path==id:
                    return ''
            if mo.group('path') is not None:
                path = str(mo.group('path'))
            if path:
                encoding = self.encoding
                if ',' in path:
                    path,encoding = path.split(',',1)
                parent_dir = os.path.dirname(parent_path)
                abs_path = os.path.join(parent_dir, path)
                self.included_paths.append(abs_path)
                if not os.path.isfile(abs_path):
                    raise NotFoundError('No template file at path %s' %abs_path)
                with open(abs_path,encoding=encoding,errors='replace') as fileobj:
                    inclusion = fileobj.read()
                try:
                    return self._include(inclusion, namespace, abs_path)
                except RuntimeError:
                    raise RecursionError( \
                        'Possible circular reference in template inclusions. Template inclusion list is:\n' + \
                        '\n'.join(self.included_paths)) 
            if mo.group('invalid') is not None:
                return mo.group(0)
        return regex.sub(helper, text)
        
    def _substitute(self, text, namespace):
        delimiter = '$'
        regex = re.compile(r"""
            \$(?:
              (?P<escaped>\$)                                             |  # Escape sequence of two delimiters
              (?P<container>[_a-z][_a-z0-9]*)\.(?P<attr>[_a-z][_a-z0-9]*) |  # a container  with attribute                     
              (?P<named>[_a-z][_a-z0-9]*)                                 |  # a Python identifier
              (?P<invalid>)                                                  # Other ill-formed delimiter exprs
            )
            """, re.IGNORECASE | re.VERBOSE | re.UNICODE)
        def helper(mo):
            named = mo.group('named')
            if named is not None:
                try:
                    res = namespace[named]
                except KeyError:
                    return delimiter + named
                # make sure res is a string (8-bit or unicode) and not an instance. 
                return '%s' % res  
            container = mo.group('container')
            if container is not None:
                if not container in namespace:
                    return mo.group(0)
                obj = namespace[container]
                attr = mo.group('attr')
                try:
                    res = getattr(obj, attr)
                except AttributeError:
                    try:
                        res = obj[attr]
                    except:
                        res = mo.group(0)
                # make sure res is a string (8-bit or unicode) and not an instance. 
                return '%s' % res
            if mo.group('escaped') is not None:
                return delimiter
            if mo.group('invalid') is not None:
                return delimiter
        return regex.sub(helper, text)

    def _translate(self, text):
        regex = re.compile(r"""
            _(?:
                (?P<escaped>_)                 |   # Escape sequence of two delimiters
                \[(?P<string>.*?[^\\])\]       |   # a bracketed string to translate
                (?P<invalid>)                      # Other ill-formed delimiter exprs
            )
            """, re .IGNORECASE | re.VERBOSE)
        def helper(mo):
            if mo.group('escaped') is not None:
                return mo.group(0)
            if mo.group('string') is not None:
                val = str(mo.group('string')).replace('\]', ']')
                return self.translation_func(val)
            if mo.group('invalid') is not None:
                return mo.group(0)
        return regex.sub(helper, text)
