#!/usr/bin/env python
from distutils.core import setup

import Karrigell

package_dir = { 'Karrigell':'Karrigell','HTMLTags':'HTMLTags'}
package_data = {
    'Karrigell':['*.txt'],'HTMLTags':['*.txt']
    }

setup(name='Karrigell',
      version=Karrigell.version,
      description='Web framework for Python 3.2+',
      author='Pierre Quentel',
      author_email='pierre.quentel@gmail.com',
      url='http://code.google.com/p/karrigell/',
      packages=['Karrigell','HTMLTags'],
      package_dir=package_dir,
      package_data=package_data,
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: BSD License',
          'Programming Language :: Python',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
          ]
     )
