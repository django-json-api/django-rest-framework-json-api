====================================
JSON API and Django Rest Framework
====================================

.. image:: https://travis-ci.org/django-json-api/django-rest-framework-json-api.svg?branch=develop
   :target: https://travis-ci.org/django-json-api/django-rest-framework-json-api

.. image:: https://readthedocs.org/projects/django-rest-framework-json-api/badge/?version=latest
   :alt: Read the docs
   :target: http://django-rest-framework-json-api.readthedocs.org/

.. image:: https://codeclimate.com/github/django-json-api/django-rest-framework-json-api/badges/gpa.svg
   :target: https://codeclimate.com/github/django-json-api/django-rest-framework-json-api
   :alt: Code Climate

.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/django-json-api/django-rest-framework-json-api
   :target: https://gitter.im/django-json-api/django-rest-framework-json-api


Documentation: http://django-rest-framework-json-api.readthedocs.org/

Live demo (resets every hour): http://json-api.jerel.co/

Format specification: http://jsonapi.org/format/


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

1. Django
2. Django REST Framework

------------
Installation
------------

From PyPI
^^^^^^^^^

::

    $ pip install djangorestframework-jsonapi==2.0.0-beta.1


From Source
^^^^^^^^^^^

::

    $ git clone https://github.com/django-json-api/django-rest-framework-json-api.git
    $ cd django-rest-framework-json-api && pip install -e .


Running the example app
^^^^^^^^^^^^^^^^^^^^^^^

::

    $ git clone https://github.com/django-json-api/django-rest-framework-json-api.git
    $ cd django-rest-framework-json-api && pip install -e .
    $ django-admin.py runserver --settings=example.settings

Browse to http://localhost:8000


Running Tests
^^^^^^^^^^^^^

::

    $ python runtests.py


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
