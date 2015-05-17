import os
import configparser
try:
    path = os.path.join(THIS.root_dir,'test_translations.ini')
except NameError:
    path = 'test_translations.ini'
encoding = 'utf-8'
ini = configparser.ConfigParser()
ini.read([path],encoding=encoding)

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
        return ini.get(src,'default')
    except configparser.NoOptionError:
        return src