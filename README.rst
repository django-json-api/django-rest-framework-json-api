==================================
JSON API and Django Rest Framework
==================================

.. image:: https://github.com/django-json-api/django-rest-framework-json-api/workflows/Tests/badge.svg
   :alt: Tests
   :target: https://github.com/django-json-api/django-rest-framework-json-api/actions

.. image:: https://readthedocs.org/projects/django-rest-framework-json-api/badge/?version=latest
   :alt: Read the docs
   :target: https://django-rest-framework-json-api.readthedocs.org/

.. image:: https://img.shields.io/pypi/v/djangorestframework-jsonapi.svg
   :alt: PyPi Version
   :target: https://pypi.org/project/djangorestframework-jsonapi/

--------
Overview
--------

**JSON API support for Django REST Framework**

* Documentation: https://django-rest-framework-json-api.readthedocs.org/
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
            "id": "3",
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


-----
Goals
-----

As a Django REST Framework JSON API (short DJA) we are trying to address following goals:

1. Support the `JSON API`_ spec to compliance

2. Be as compatible with `Django REST Framework`_ as possible

   e.g. issues in Django REST Framework should be fixed upstream and not worked around in DJA

3. Have sane defaults to be as easy to pick up as possible

4. Be solid and tested with good coverage

5. Be performant

.. _JSON API: http://jsonapi.org
.. _Django REST Framework: https://www.django-rest-framework.org/

------------
Requirements
------------

1. Python (3.6, 3.7, 3.8, 3.9)
2. Django (2.2, 3.0, 3.1)
3. Django REST Framework (3.12)

We **highly** recommend and only officially support the latest patch release of each Python, Django and REST Framework series.

Generally Python and Django series are supported till the official end of life. For Django REST Framework the last two series are supported.

------------
Installation
------------

From PyPI
^^^^^^^^^

::

    $ pip install djangorestframework-jsonapi
    $ # for optional package integrations
    $ pip install djangorestframework-jsonapi['django-filter']
    $ pip install djangorestframework-jsonapi['django-polymorphic']
    $ pip install djangorestframework-jsonapi['openapi']


From Source
^^^^^^^^^^^

::

    $ git clone https://github.com/django-json-api/django-rest-framework-json-api.git
    $ cd django-rest-framework-json-api
    $ pip install -e .


Running the example app
^^^^^^^^^^^^^^^^^^^^^^^

It is recommended to create a virtualenv for testing. Assuming it is already
installed and activated:

::

    $ git clone https://github.com/django-json-api/django-rest-framework-json-api.git
    $ cd django-rest-framework-json-api
    $ pip install -Ur requirements.txt
    $ django-admin migrate --settings=example.settings
    $ django-admin loaddata drf_example --settings=example.settings
    $ django-admin runserver --settings=example.settings

Browse to
* http://localhost:8000 for the list of available collections (in a non-JSONAPI format!),
* http://localhost:8000/swagger-ui/ for a Swagger user interface to the dynamic schema view, or
* http://localhost:8000/openapi for the schema view's OpenAPI specification document.


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
            'rest_framework_json_api.pagination.JsonApiPageNumberPagination',
        'DEFAULT_PARSER_CLASSES': (
            'rest_framework_json_api.parsers.JSONParser',
            'rest_framework.parsers.FormParser',
            'rest_framework.parsers.MultiPartParser'
        ),
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework_json_api.renderers.JSONRenderer',
            'rest_framework_json_api.renderers.BrowsableAPIRenderer',
        ),
        'DEFAULT_METADATA_CLASS': 'rest_framework_json_api.metadata.JSONAPIMetadata',
        'DEFAULT_FILTER_BACKENDS': (
            'rest_framework_json_api.filters.QueryParameterValidationFilter',
            'rest_framework_json_api.filters.OrderingFilter',
            'rest_framework_json_api.django_filters.DjangoFilterBackend',
            'rest_framework.filters.SearchFilter',
        ),
        'SEARCH_PARAM': 'filter[search]',
        'TEST_REQUEST_RENDERER_CLASSES': (
            'rest_framework_json_api.renderers.JSONRenderer',
        ),
        'TEST_REQUEST_DEFAULT_FORMAT': 'vnd.api+json'
    }

This package provides much more including automatic inflection of JSON keys, extra top level data (using nested
serializers), relationships, links, paginators, filters, and handy shortcuts.
Read more at http://django-rest-framework-json-api.readthedocs.org/
