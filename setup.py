#!/usr/bin/env python
import os
from setuptools import setup, find_packages


def get_readme():
    """
    Get the readme
    """
    return open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()


setup(
    name='rest_framework_ember',
    version='1.3.2',
    description="A Django Rest Framework adapter that provides Ember Data \
        support. When jsonapi.org reaches 1.0 this adapter plans to adopt it.",
    long_description=get_readme(),
    url='https://github.com/django-json-api/rest_framework_ember',
    license='BSD',
    keywords="EmberJS Ember Data Django REST",
    packages=find_packages(),
    install_requires=['django', 'djangorestframework >= 2.4.0', 'inflection'],
    platforms=['any'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
