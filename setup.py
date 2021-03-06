# -*- coding:utf-8 -*-

import os
import sys


from setuptools import setup, find_packages
here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.rst')) as f:
        README = f.read()
    with open(os.path.join(here, 'CHANGES.txt')) as f:
        CHANGES = f.read()
except IOError:
    README = CHANGES = ''


install_requires = [
    'django-mindscape',
    'factory_boy',
    'prestring',
]

full_extras = [
    'django-model-utils',
    'autopep8'
]

docs_extras = [
]

tests_require = [
]

testing_extras = tests_require + [
    'django-model-utils',
    'autopep8'
]

setup(name='django-fixtureboy',
      version='0.1',
      description='a helper to use factory boy with django',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python",
          "Programming Language :: Python :: Implementation :: CPython",
      ],
      keywords='',
      author="",
      author_email="",
      url="",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=install_requires,
      extras_require={
          'testing': testing_extras,
          'docs': docs_extras,
          'full': full_extras
      },
      tests_require=tests_require,
      test_suite="django_fixtureboy.tests",
      entry_points="""
""")
