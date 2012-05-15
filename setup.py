from setuptools import setup, find_packages
import os

version = '2.0dev'

tests_require = [
    'Products.Silva [test]',
    'silva.demo.contentlayout',
    ]

setup(name='silva.core.contentlayout',
      version=version,
      description="Silva Content Layout base functionality",
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
      url='',
      license='GPL',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      namespace_packages=['silva', 'silva.core'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'silva.core.interfaces',
          'silva.core.services',
          'silva.core.conf',
          'silva.core.references',
          'silva.core.views',
          'zeam.component',
          'zeam.form.silva',
          'zope.component',
          'zope.event',
          'zope.interface',
          'zope.schema',
      ],
      tests_require = tests_require,
      extras_require = {'test': tests_require},
      entry_points="""
      [silva.ui.resources]
      editor = silva.core.contentlayout.interfaces:IEditorResources
      """,

      )
