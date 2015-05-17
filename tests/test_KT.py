#!python3.2
if __name__ == "__main__":
    # Test use of KT as a stand-alone template engine
    # Note: translations not tested
    import os, sys
    cwd = os.getcwd()
    sys.path.insert(0,cwd)
    sys.path.insert(0,os.path.dirname(cwd))
    print(sys.path)
    from Karrigell.KT import KT
    kt = KT(templ_dir='test_templates')
    phrase = 'phrase to translate'
    var = 'value of variable "var"'
    THIS = {'root_url':'/'}
    print(kt.render('parent.kt', data=locals(), this=THIS))
else: 
    # Test within Karrigell framework
    # Change language in brwoser from en to fr to test translations
    translations = Import('test_translations.py')
    _ = translations.translate
    ENCODING=translations.encoding
    kt = KT(translate=_, encoding=ENCODING)

def index():
    phrase = 'phrase to translate'
    var = 'value of variable "var"'
    return kt.render('test_templates/parent.kt', data=locals(), this=THIS)


    