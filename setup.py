from setuptools import setup, find_packages
import os
 
version = '1.0.4'

setup(name='silva.core.contentlayout',
      version=version,
      description="content layout base functionality",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='Andrew Altepeter',
      author_email='aaltepet@bethel.edu',
      url='',
      license='GPL',
      packages=find_packages(),
      namespace_packages=['silva', 'silva.core'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'silva.core.interfaces',
          'silva.core.services',
          'silva.core.conf',
          'silva.core.cache',
          'bethel.core.zopecache'
      ],
      entry_points="""
      [zodbupdate]
      renames = silva.core.contentlayout:CLASS_CHANGES
      """
      )
