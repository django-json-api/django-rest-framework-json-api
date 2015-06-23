====================================
Ember Data and Django Rest Framework
====================================

.. image:: https://travis-ci.org/django-json-api/rest_framework_ember.svg?branch=master
   :target: https://travis-ci.org/django-json-api/rest_framework_ember

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


Running Tests
^^^^^^^^^^^^^

::

    $ python runtests.py


-----
Usage
-----


``rest_framework_ember`` assumes you are using class-based views in Django
Rest Framework.


Settings
^^^^^^^^

One can either add ``rest_framework_ember.parsers.JSONParser`` and
``rest_framework_ember.renderers.JSONRenderer`` to each ``ViewSet`` class, or
override ``settings.REST_FRAMEWORK``::


    REST_FRAMEWORK = {
        'PAGINATE_BY': 10,
        'PAGINATE_BY_PARAM': 'page_size',
        'MAX_PAGINATE_BY': 100,
        # DRF v3.1+
        'DEFAULT_PAGINATION_CLASS':
            'rest_framework_ember.pagination.PageNumberPagination',
        # older than DRF v3.1
        'DEFAULT_PAGINATION_SERIALIZER_CLASS':
            'rest_framework_ember.pagination.PaginationSerializer',
        'DEFAULT_PARSER_CLASSES': (
            'rest_framework_ember.parsers.JSONParser',
            'rest_framework.parsers.FormParser',
            'rest_framework.parsers.MultiPartParser'
        ),
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework_ember.renderers.JSONRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
        ),
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


Ember Data <-> Rest Framework Format Conversion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*(camelization/underscore/pluralize)*

This package includes the optional ability to automatically convert json requests
and responses from the Ember Data camelCase to python/rest_framework's preferred
underscore. Additionally resource names can be pluralized when an array of objects
are returned. To hook this up include the following in your project settings::

   REST_EMBER_FORMAT_KEYS = True
   REST_EMBER_PLURALIZE_KEYS = True

Note: due to the way the inflector works address_1 will convert to address1
on output but cannot convert address1 back to address_1 on POST or PUT. Keep
this in mind when naming fields with numbers in them.


Example - Without format conversion::

   {
      "identity": [
         {
            "id": 1,
            "username": "john",
            "first_name": "John",
            "last_name": "Coltrane"
         },
         {
            "id": 2,
            "username": "frodo",
            "first_name": "Bilbo",
            "last_name": "Baggins"
         },
      ],
      ...
   }

Example - With format conversion::

   {
      "identities": [
         {
            "id": 1,
            "username": "john",
            "firstName": "John",
            "lastName": "Coltrane"
         },
         {
            "id": 2,
            "username": "frodo",
            "firstName": "Bilbo",
            "lastName": "Baggins"
         },
      ],
      ...
   }


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

Displaying Server Side Validation Messages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ember Data does not ship with a default implementation of a validation error
handler except in the Rails ActiveModelAdapter so to display validation errors
you will need to add a small client adapter::

    App.ApplicationAdapter = DS.RESTAdapter.extend({
      ajaxError: function(jqXHR) {
        var error = this._super(jqXHR);
        if (jqXHR && jqXHR.status === 400) {
          var response = Ember.$.parseJSON(jqXHR.responseText),
              errors = {},
              keys = Ember.keys(response);
          if (keys.length === 1) {
            var jsonErrors = response[keys[0]];
            Ember.EnumerableUtils.forEach(Ember.keys(jsonErrors), function(key) {
              errors[key] = jsonErrors[key];
            });
          }
          return new DS.InvalidError(errors);
        } else {
          return error;
        }
      }
    });

The adapter above will handle the following response format when the response has
a 400 status code. The root key ("post" in this example) is discarded::

    {
      "post": {
        "slug": ["Post with this Slug already exists."]
      }
    }

To display all errors add the following to the template::

    {{#each message in errors.messages}}
      {{message}}
    {{/each}}

To display a specific error inline use the following::

    {{#each errors.title}}
      <div class="error">{{message}}</div>
    {{/each}}
    {{input name="title" value=title}}


---------------------
Sideloading Resources
---------------------

If you are using the JSON Renderer globally, this can lead to issues
when hitting endpoints that are intended to sideload other objects.

For example::

    {
        "users": [],
        "cars": []
    }


Set the ``resource_name`` property on the object to ``False``, and the data
will be returned as it is above.


------
Mixins
------

The following mixin classes are available to use with Rest Framework
resources.

rest_framework_ember.mixins.MultipleIDMixin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Overrides ``get_queryset`` to filter by ``ids[]`` in URL query params.

