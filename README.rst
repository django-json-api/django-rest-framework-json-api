====================================
Ember Data and Django Rest Framework
====================================

.. image:: https://travis-ci.org/ngenworks/rest_framework_ember.svg?branch=master
   :target: https://travis-ci.org/ngenworks/rest_framework_ember

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
            "next_link": "http://example.com/api/1.0/identities/?page=2",
            "page": 1,
            "previous": null,
            "previous_link": null
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

    pip install rest_framework_ember


From Source
^^^^^^^^^^^

::

    $ git clone https://github.com/ngenworks/rest_framework_ember.git
    $ cd rest_framework_ember && pip install -e .


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
        'PAGINATE_BY_PARAM': 'page_size',
        'MAX_PAGINATE_BY': 100,
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


If ``PAGINATE_BY`` is set the renderer will return a ``meta`` object with
record count and the next and previous links. Django Rest Framework looks
for the ``page`` GET parameter by default allowing you to make requests for
subsets of the data with ``this.store.find('identity', {page: 2});``.


resource_name property
^^^^^^^^^^^^^^^^^^^^^^

On resources that do not subclass ``rest_framework.viewsets.ModelViewSet``,
the ``resource_name`` property is required on the class::

    class Me(generics.GenericAPIView):
        """
        Current user's identity endpoint.

        GET /me
        """
        resource_name = 'data'
        serializer_class = identity_serializers.IdentitySerializer
        allowed_methods = ['GET']
        permission_classes = (permissions.IsAuthenticated, )


Managing the trailing slash
^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default Django expects a trailing slash on urls and will 301 redirect any
requests lacking a trailing slash. You can change the server side by
instantiating the Django REST Framework's router like so::

    router = routers.SimpleRouter(trailing_slash=False)

If you aren't using SimpleRouter you can instead set APPEND_SLASH = False
in Django's settings.py file and modify url pattern regex to match routes
without a trailing slash.

If you prefer to make the change on the client side then add an
application adapter to your Ember app and override the buildURL method::

    App.ApplicationAdapter = DS.RESTAdapter.extend({
      buildURL: function() {
        var url = this._super.apply(this, arguments);
        if (url.charAt(url.length -1) !== '/') {
          url += '/';
        }
        return url;
      }
    });

