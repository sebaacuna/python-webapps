#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name='webapps',
      version='0.2',
      packages=find_packages(),
      package_data={'webapps': ['data_files/conf/*.*' ]},
      exclude_package_data={'webapps': ['bin/*.pyc']},
      #scripts=['bookie/bin/manage.py']
      )
