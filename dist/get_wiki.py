import sys
import os
import re
import shutil
import urllib.request

parent = os.path.dirname(os.getcwd())
sys.path.insert(0,os.path.join(parent,'trunk'))
from Karrigell import version

proxies = {}
if os.path.exists('proxy.dat'):
    proxies = {'http':open('proxy.dat').read()}

proxy_handler = urllib.request.ProxyHandler(proxies=proxies)
opener = urllib.request.build_opener(proxy_handler)

url = "http://code.google.com/p/karrigell/w/list"
req = opener.open(url)
src = req.read().decode('utf-8')
pages = []
for mo in re.finditer('(?s)<td class="vt id col_0"><a href="/p/karrigell/wiki/(.*?)">(.*?)</a></td>',src):
    pages.append(mo.groups()[0])

if os.path.exists('doc'):
    for path in os.listdir('doc'):
        if path.endswith('.html'):
            os.remove(os.path.join('doc',path))
else:
    os.mkdir('doc')
    os.mkdir(os.path.join('doc','images'))
    for path in ['wiki.css','prettify.js']:
        shutil.copyfile(path,os.path.join('doc',path))
    for path in os.listdir('images'):
        if not path.endswith('.gif'):
            continue
        shutil.copyfile(os.path.join('images',path),
            os.path.join('doc','images',path))
        
for page in pages:
    print(page,'...')
    url = "http://code.google.com/p/karrigell/wiki/%s?show=content,sidebar" %page
    req = opener.open(url)

    src = req.read().decode('utf-8')

    src = src.replace('http://www.gstatic.com/codesite/ph/images/','images/')
    src = re.sub('/p/karrigell/wiki/(.*?)"',r'\1.html"',src)
    src = re.sub('(?s)<div style="float:right;">(.*?)</div>','',src)
    src = re.sub('(?s)<div class="ifCollapse"(.*?)</div>','',src)
    src = re.sub('(?s)<div class="ifExpand"(.*?)Edit(.*?)</div>','',src)
    src = re.sub('(?s)<div id="wikiauthor"(.*?)</div>','',src)
    src = re.sub('(?s)<img (.*?)star_off.gif(.*?)>','',src)
    src = re.sub('(?s)<a class="label" (.*?)>Featured</a>','',src)
    src = re.sub('(?s)<div id="wikiheader">(.*?)<div>(.*?)</div>(.*?)</div>','',src)

    stylesheet = '<link rel="stylesheet" href="wiki.css">\n'
    meta = '<meta http-equiv="Content-type" content="text/html;charset=utf-8">\n'

    src = src.replace('<head>','<head>\n'+stylesheet+meta)
    
    title = '<div id="title">Karrigell-%s documentation</div>\n' %version
    src = src.replace('<body>','<body>\n'+title)

    prettify = """<script src="prettify.js"></script>
     <script type="text/javascript">
     prettyPrint();
     </script>
    """
    src = src.replace('</body>',prettify+'</body>')

    out = open(os.path.join('doc','%s.html' %page),'w',encoding="utf-8")
    out.write(src)
    out.close()
