#!/usr/bin/env python3

import os
import re
import sys

from setuptools import setup

needs_wheel = {"bdist_wheel"}.intersection(sys.argv)
wheel = ["wheel"] if needs_wheel else []


def read(*paths):
    """
    Build a file path from paths and return the contents.
    """
    with open(os.path.join(*paths)) as f:
        return f.read()


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, "__init__.py")).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [
        dirpath
        for dirpath, dirnames, filenames in os.walk(package)
        if os.path.exists(os.path.join(dirpath, "__init__.py"))
    ]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [
        (dirpath.replace(package + os.sep, "", 1), filenames)
        for dirpath, dirnames, filenames in os.walk(package)
        if not os.path.exists(os.path.join(dirpath, "__init__.py"))
    ]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename) for filename in filenames])
    return {package: filepaths}


if sys.argv[-1] == "publish":
    os.system("python setup.py sdist upload")
    os.system("python setup.py bdist_wheel upload")
    print("You probably want to also tag the version now:")
    print(
        "  git tag -a {0} -m 'version {0}'".format(
            get_version("rest_framework_json_api")
        )
    )
    print("  git push --tags")
    sys.exit()

setup(
    name="djangorestframework-jsonapi",
    version=get_version("rest_framework_json_api"),
    url="https://github.com/django-json-api/django-rest-framework-json-api",
    license="BSD",
    description="A Django REST framework API adapter for the JSON:API spec.",
    long_description=read("README.rst"),
    author="Jerel Unruh",
    author_email="",
    packages=get_packages("rest_framework_json_api"),
    package_data=get_package_data("rest_framework_json_api"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    install_requires=[
        "inflection>=0.5.0",
        "djangorestframework>=3.12,<3.14",
        "django>=2.2,<4.1",
    ],
    extras_require={
        "django-polymorphic": ["django-polymorphic>=3.0"],
        "django-filter": ["django-filter>=2.4"],
        "openapi": ["pyyaml>=5.4", "uritemplate>=3.0.1"],
    },
    setup_requires=wheel,
    python_requires=">=3.7",
    zip_safe=False,
)
