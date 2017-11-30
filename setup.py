#!/usr/bin/env python
from __future__ import print_function

import os
import re
import sys

from setuptools import setup

needs_mock = sys.version_info < (3, 3)
mock = ['mock'] if needs_mock else []
needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []
needs_sphinx = {'build_sphinx', 'upload_docs'}.intersection(sys.argv)
sphinx = ['sphinx'] if needs_sphinx else []
needs_wheel = {'bdist_wheel'}.intersection(sys.argv)
wheel = ['wheel'] if needs_wheel else []


def read(*paths):
    """
    Build a file path from paths and return the contents.
    """
    with open(os.path.join(*paths), 'r') as f:
        return f.read()


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


if sys.argv[-1] == 'publish':
    os.system("python setup.py sdist upload")
    os.system("python setup.py bdist_wheel upload")
    print("You probably want to also tag the version now:")
    print("  git tag -a {0} -m 'version {0}'".format(
        get_version('rest_framework_json_api')))
    print("  git push --tags")
    sys.exit()

setup(
    name='djangorestframework-jsonapi',
    version=get_version('rest_framework_json_api'),
    url='https://github.com/django-json-api/django-rest-framework-json-api',
    license='MIT',
    description='A Django REST framework API adapter for the JSON API spec.',
    long_description=read('README.rst'),
    author='Jerel Unruh',
    author_email='',
    packages=get_packages('rest_framework_json_api'),
    package_data=get_package_data('rest_framework_json_api'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    install_requires=[
        'inflection>=0.3.0',
        'djangorestframework>=3.1.0',
        'django',
    ],
    setup_requires=pytest_runner + sphinx + wheel,
    tests_require=[
        'pytest-factoryboy',
        'factory-boy<2.9.0',
        'pytest-django',
        'pytest>=2.8,<3',
        'django-polymorphic',
        'packaging',
        'django-debug-toolbar'
    ] + mock,
    zip_safe=False,
)
