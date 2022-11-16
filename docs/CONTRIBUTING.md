# Contributing

Django REST framework JSON:API (aka DJA)  should be easy to contribute to.
If anything is unclear about how to contribute,
please submit an issue on GitHub so that we can fix it!

Before writing any code, have a conversation on a GitHub issue to see
if the proposed change makes sense for the project.

## Setup development environment

### Clone

To start developing on Django REST framework JSON:API you need to first clone the repository:

    git clone https://github.com/django-json-api/django-rest-framework-json-api.git

### Testing

To run tests clone the repository, and then:

     # Setup the virtual environment
     python3 -m venv env
     source env/bin/activate
     pip install -r requirements.txt

     # Format code
     black .

     # Run linting
     flake8

     # Run tests
     pytest

### Running against multiple environments

You can also use the excellent [tox](https://tox.readthedocs.io/en/latest/) testing tool to run the tests against all supported versions of Python and Django.  Install `tox` globally, and then simply run:

    tox


### Setup pre-commit

pre-commit hooks is an additional option to check linting and formatting of code independent of
an editor before you commit your changes with git.

To setup pre-commit hooks first create a testing environment as explained above before running below commands:

    pip install pre-commit
    pre-commit install

## For maintainers

### Create release

To upload a release (using version 1.2.3 as the example) first setup testing environment as above before running below commands:

    python setup.py sdist bdist_wheel
    twine upload dist/*
    git tag -a v1.2.3 -m 'Release 1.2.3'
    git push --tags


### Add maintainer

In case a new maintainer joins our team we need to consider to what of following services we want to add them too:

* [Github organization](https://github.com/django-json-api)
* [Read the Docs project](https://django-rest-framework-json-api.readthedocs.io/)
* [PyPi project](https://pypi.org/project/djangorestframework-jsonapi/)
