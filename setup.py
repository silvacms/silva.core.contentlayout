# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt
from setuptools import setup, find_packages
import os

version = '3.0.5'

tests_require = [
    'Products.Silva [test]',
    'silva.demo.contentlayout',
    ]

setup(name='silva.core.contentlayout',
      version=version,
      description="Silva Content Layout engine for Silva CMS",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Zope2",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Andrew Altepeter',
      author_email='aaltepet@bethel.edu',
      url='https://github.com/silvacms/silva.core.contentlayout',
      license='GPL',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      namespace_packages=['silva', 'silva.core'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'five.grok',
          'grokcore.chameleon',
          'grokcore.component',
          'grokcore.view',
          'setuptools',
          'silva.core.conf',
          'silva.core.editor',
          'silva.core.interfaces',
          'silva.core.references',
          'silva.core.services',
          'silva.core.views',
          'silva.core.xml',
          'silva.ui',
          'zeam.component',
          'zeam.form.silva',
          'zope.annotation',
          'zope.cachedescriptors',
          'zope.component',
          'zope.event',
          'zope.i18n',
          'zope.interface',
          'zope.intid',
          'zope.lifecycleevent',
          'zope.publisher',
          'zope.schema',
          'zope.traversing',
      ],
      tests_require = tests_require,
      extras_require = {'test': tests_require},
      entry_points="""
      [silva.ui.resources]
      editor = silva.core.contentlayout.interfaces:IEditorResources
      """,

      )
