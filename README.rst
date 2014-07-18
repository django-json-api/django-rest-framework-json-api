===============================
Ember Data and Django Rest Framework
===============================

The default Ember Data REST Adapter conventions differ from the default
Django Rest Framework JSON request and response format. Instead of adding
a Django specific adapter to Ember Data we use this adapter in Django to
output and accept JSON in the format the Ember Data REST Adapter expects.

By default, Django REST Framework will produce a response like::

    {
        "count": 20,
        "next": "http://example.com/api/1.0/identities/?page=2",
        "previous": null,
        "results": [
            {
                "id": 1,
                "username": "john",
                "full_name": "John Coltrane"
            },
            {
                ...
            }
        ]
    }


However, for an ``identity`` model in EmberJS, the Ember Data REST Adapter
expects a response to look like the following::

    {
        "identity": [
            {
                "id": 1,
                "username": "john",
                "full_name": "John Coltrane"
            },
            {
                ...
            }
        ],
        "meta": {
            "count": 20,
            "next": 2,
            "nextLink": "http://example.com/api/1.0/identities/?page=2",
            "previous": null,
            "prevousLink": null
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

::

    pip install rest_framework_ember


-----
Usage
-----


``rest_framework_ember`` assumes you are using class-based views in Django 
Rest Framework.


Settings
^^^^^^^^

One can either add ``rest_framework_ember.parsers.EmberJSONParser`` and 
``rest_framework_ember.renderers.JSONRenderer`` to each ``ViewSet`` class, or
override ``settings.REST_FRAMEWORK``::


    REST_FRAMEWORK = {
        'PAGINATE_BY': 10,
        'DEFAULT_PAGINATION_SERIALIZER_CLASS':
            'rest_framework_ember.pagination.EmberPaginationSerializer',
        'DEFAULT_PARSER_CLASSES': (
            'rest_framework_ember.parsers.EmberJSONParser',
            'rest_framework.parsers.FormParser',
            'rest_framework.parsers.MultiPartParser'
        ),
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework_ember.renderers.JSONRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
        ),
        'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    }


If PAGINATE_BY is included the renderer will return a ``meta`` object with
record count and the next and previous links.


resource_name property
^^^^^^^^^^^^^^^^^^^^^^

On resources that do not subclass ``rest_framework.viewsets.ModelViewSet``,
the ``resource_name`` property is required on the class.::

    class Me(generics.GenericAPIView):
        """
        Current user's identity endpoint.

        GET /me
        """
        resource_name = 'data'
        serializer_class = identity_serializers.IdentitySerializer
        allowed_methods = ['GET']
        permission_classes = (permissions.IsAuthenticated, )




