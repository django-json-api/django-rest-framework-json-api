===============================
Ember and Django Rest Framework
===============================

EmberJS is extremely opinionated on how JSON REST requests and responses
should look. Going against the grain can lead to frustrated Javascript
developers.

By default, Django REST Framework will produce a response like::

    {
        "id": 1,
        "username": "john",
        "full_name": "John Coltrane"
    }


However, if this is an ``identity`` model in EmberJS, Ember expects a
response to look like the following::

    {
        "identity": {
            "id": 1,
            "username": "john",
            "full_name": "John Coltrane"
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




