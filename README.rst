====================================
JSON API and Django Rest Framework
====================================

.. image:: https://travis-ci.org/django-json-api/django-rest-framework-json-api.svg?branch=master
   :target: https://travis-ci.org/django-json-api/django-rest-framework-json-api

.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/django-json-api/django-rest-framework-json-api
   :target: https://gitter.im/django-json-api/django-rest-framework-json-api?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

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

    pip install rest_framework_json_api


From Source
^^^^^^^^^^^

::

    $ git clone https://github.com/django-json-api/rest_framework_json_api.git
    $ cd rest_framework_json_api && pip install -e .


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
override ``settings.REST_FRAMEWORK``::


    REST_FRAMEWORK = {
        'PAGINATE_BY': 10,
        'PAGINATE_BY_PARAM': 'page_size',
        'MAX_PAGINATE_BY': 100,
        # DRF v3.1+
        'DEFAULT_PAGINATION_CLASS':
            'rest_framework_json_api.pagination.PageNumberPagination',
        # older than DRF v3.1
        'DEFAULT_PAGINATION_SERIALIZER_CLASS':
            'rest_framework_json_api.pagination.PaginationSerializer',
        'DEFAULT_PARSER_CLASSES': (
            'rest_framework_json_api.parsers.JSONParser',
            'rest_framework.parsers.FormParser',
            'rest_framework.parsers.MultiPartParser'
        ),
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework_json_api.renderers.JSONRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
        ),
    }

If ``PAGINATE_BY`` is set the renderer will return a ``meta`` object with
record count and a ``links`` object with the next and previous links. Pages
can be specified with the ``page`` GET parameter.

resource_name property
^^^^^^^^^^^^^^^^^^^^^^

You may manually set the ``resource_name`` property on views or serializers to
specify the ``type`` key in the json output. It is automatically set for you as the
plural of the view or model name except on resources that do not subclass
``rest_framework.viewsets.ModelViewSet``::

    class Me(generics.GenericAPIView):
        """
        Current user's identity endpoint.

        GET /me
        """
        resource_name = 'users'
        serializer_class = identity_serializers.IdentitySerializer
        allowed_methods = ['GET']
        permission_classes = (permissions.IsAuthenticated, )


Object Key Formats
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
*(dasherize/camelize/underscore/pluralize)*

This package includes the ability (off by default) to automatically convert json
requests and responses from the python/rest_framework's preferred underscore to
a format of your choice. To hook this up include the following in your project
settings::

   JSON_API_FORMAT_KEYS = 'dasherize'

Note: due to the way the inflector works address_1 can camelize to address1
on output but it cannot convert address1 back to address_1 on POST or PUT. Keep
this in mind when naming fields with numbers in them.


Example - Without format conversion::

   {
        "data": [{
            "type": "identities",
            "id": 3,
            "attributes": {
                "username": "john",
                "first_name": "John",
                "last_name": "Coltrane",
                "full_name": "John Coltrane"
            },
        }],
        "meta": {
            "pagination": {
              "count": 20
            }
        }
   }

Example - With format conversion set to ``dasherize``::

   {
        "data": [{
            "type": "identities",
            "id": 3,
            "attributes": {
                "username": "john",
                "first-name": "John",
                "last-name": "Coltrane",
                "full-name": "John Coltrane"
            },
        }],
        "meta": {
            "pagination": {
              "count": 20
            }
        }
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
will be returned without modification.


------
Mixins
------

The following mixin classes are available to use with Rest Framework
resources.

rest_framework_json_api.mixins.MultipleIDMixin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Overrides ``get_queryset`` to filter by ``ids[]`` in URL query params.
