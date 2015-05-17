import os
import configparser
path = os.path.join(THIS.root_dir,'translations.ini')
encoding = 'iso-8859-1'
default_language='en'
ini = configparser.ConfigParser()
try:
    ini.read([path],encoding=encoding)
except:
    ini.read([path]) # encoding is not supported by Python3.1
try:
    default_language = ini.get('__default__','default_language')
except configparser.NoSectionError:
    pass
except configparser.NoOptionError:
    pass
    
def translate(src):
    if not ini.has_section(src):
        return src
    langs = REQUEST_HEADERS.get('Accept-language').split(',')
    for lang in langs:
        lang = lang.split(';')[0]
        lang = lang.split('-')[0]
        try:
            return ini.get(src,lang)
        except configparser.NoOptionError:
            continue
    try:
        return ini.get(src,default_language)
    except configparser.NoOptionError:
        pass 
    try:
        return ini.get(src,'default')
    except configparser.NoOptionError:
        return src 
