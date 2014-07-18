#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='rest_framework_ember',
    version='1.0',
    description="Make EmberJS and Django Rest Framework play nice together.",
    author="nGen Works",
    author_email='tech@ngenworks.com',
    url='http://www.ngenworks.com',
    license='BSD',
    keywords="EmberJS Django REST",
    packages=find_packages(),
    install_requires=['django', 'djangorestframework' ],
)

