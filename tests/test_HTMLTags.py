# -*- coding: iso-8859-1 -*-
import sys
import os

import unittest

# modify sys.path to use this version of HTMLTags
cwd = os.getcwd()
sys.path.insert(0,os.path.join(os.path.dirname(cwd),'trunk'))

from HTMLTags import *

class Tester(unittest.TestCase):


    def testGetByAttr1(self):
        head = HEAD(TITLE('Test document'))
        body = BODY()
        body <= H1('This is a test document')
        lines = 'First line' + BR() + 'Second line'+DIV(H1("zone"),name="zone")
        body <= lines
        html = HTML(head+body)
        self.assertEqual(lines.get_by_attr(name="zone"),
            body.get_by_attr(name="zone"))
        tags = body.get(H1)
        self.assertEqual(len(tags),2)

    def testAddMult(self):
        line = TD(B('d')+2*I('a'))*3
        self.assertEqual(str(line),
            "<td>\n<b>d</b><i>a</i><i>a</i></td>\n"*3)

    def testSelect1(self):
        formats = ['DEFAULT','DATE (YYYY-MM-DD)',
            'TIME (HH:MM:SS)','TIMESTAMP (YYY-MM-DD HH:MM:SS)']
        sf = SELECT().from_list(formats)
        options = sf.get_by_tag('OPTION')
        self.assertEqual(len(options),len(formats))
        for i,(option,format) in enumerate(zip(options,formats)):
            self.assertEqual(option.children[0],format)
            self.assertEqual(option['value'],i)
        sf.select(content='TIME (HH:MM:SS)')
        self.assertEqual(options[2]['SELECTED'],True)

    def testSelect2(self):
        s = SELECT(name="foo",MULTIPLE=True).from_list(['a','b','c','e'])
        s.select(content=['b','d'])
        options = s.get(OPTION)
        self.assertEqual(options[1]['SELECTED'],True)

    def testMult(self):
        data = TH('x')*3
        self.assertEqual(str(data),'<th>\nx</th>\n'*3)

    def testGet(self):
        t = TABLE()
        t <= TR(TD('&nbsp')+TH('Value in k€')+
                TD(DIV(Id="histo"),rowspan=5,style="background-color:red"))
        histo = t.get(Id="histo")[0]

if __name__=="__main__":
    unittest.main()