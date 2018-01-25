==================================
JSON API and Django Rest Framework
==================================

.. image:: https://travis-ci.org/django-json-api/django-rest-framework-json-api.svg?branch=develop
   :target: https://travis-ci.org/django-json-api/django-rest-framework-json-api

.. image:: https://readthedocs.org/projects/django-rest-framework-json-api/badge/?version=latest
   :alt: Read the docs
   :target: http://django-rest-framework-json-api.readthedocs.org/

.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/django-json-api/django-rest-framework-json-api
   :target: https://gitter.im/django-json-api/django-rest-framework-json-api

--------
Overview
--------

**JSON API support for Django REST Framework**

* Documentation: http://django-rest-framework-json-api.readthedocs.org/
* Format specification: http://jsonapi.org/format/


By default, Django REST Framework will produce a response like::

    {
        "count": 20,
        "next": "http://example.com/api/1.0/identities/?page=3",
        "previous": "http://example.com/api/1.0/identities/?page=1",
        "results": [{
            "id": 3,
            "username": "john",
            "full_name": "John Coltrane"
        }]
    }


However, for an ``identity`` model in JSON API format the response should look
like the following::

    {
        "links": {
            "prev": "http://example.com/api/1.0/identities",
            "self": "http://example.com/api/1.0/identities?page=2",
            "next": "http://example.com/api/1.0/identities?page=3",
        },
        "data": [{
            "type": "identities",
            "id": 3,
            "attributes": {
                "username": "john",
                "full-name": "John Coltrane"
            }
        }],
        "meta": {
            "pagination": {
              "count": 20
            }
        }
    }


------------
Requirements
------------

1. Python (2.7, 3.4, 3.5, 3.6)
2. Django (1.11, 2.0)
3. Django REST Framework (3.6, 3.7)

------------
Installation
------------

From PyPI
^^^^^^^^^

::

    $ pip install djangorestframework-jsonapi


From Source
^^^^^^^^^^^

::

    $ git clone https://github.com/django-json-api/django-rest-framework-json-api.git
    $ cd django-rest-framework-json-api
    $ pip install -e .


Running the example app
^^^^^^^^^^^^^^^^^^^^^^^

::

    $ git clone https://github.com/django-json-api/django-rest-framework-json-api.git
    $ cd django-rest-framework-json-api
    $ pip install -e .
    $ django-admin.py runserver --settings=example.settings

Browse to http://localhost:8000


Running Tests
^^^^^^^^^^^^^

It is recommended to create a virtualenv for testing. Assuming it is already
installed and activated:

::

    $ pip install -e .
    $ pip install -r requirements-development.txt
    $ py.test


-----
Usage
-----


``rest_framework_json_api`` assumes you are using class-based views in Django
Rest Framework.


Settings
^^^^^^^^

One can either add ``rest_framework_json_api.parsers.JSONParser`` and
``rest_framework_json_api.renderers.JSONRenderer`` to each ``ViewSet`` class, or
override ``settings.REST_FRAMEWORK``

::

    REST_FRAMEWORK = {
        'PAGE_SIZE': 10,
        'EXCEPTION_HANDLER': 'rest_framework_json_api.exceptions.exception_handler',
        'DEFAULT_PAGINATION_CLASS':
            'rest_framework_json_api.pagination.PageNumberPagination',
        'DEFAULT_PARSER_CLASSES': (
            'rest_framework_json_api.parsers.JSONParser',
            'rest_framework.parsers.FormParser',
            'rest_framework.parsers.MultiPartParser'
        ),
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework_json_api.renderers.JSONRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
        ),
        'DEFAULT_METADATA_CLASS': 'rest_framework_json_api.metadata.JSONAPIMetadata',
    }

If ``PAGINATE_BY`` is set the renderer will return a ``meta`` object with
record count and a ``links`` object with the next and previous links. Pages
can be specified with the ``page`` GET parameter.

This package provides much more including automatic inflection of JSON keys, extra top level data (using nested serializers), relationships, links, and handy shortcuts like MultipleIDMixin. Read more at http://django-rest-framework-json-api.readthedocs.org/
