
# Usage

The DJA package implements a custom renderer, parser, exception handler, and
pagination. To get started enable the pieces in `settings.py` that you want to use.

### Configuration
We suggest that you simply copy the settings block below and modify it if necessary.
``` python
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
```

If `PAGINATE_BY` is set the renderer will return a `meta` object with
record count and a `links` object with the next, previous, first, and last links.
Pages can be selected with the `page` GET parameter.

### Setting the resource_name

You may manually set the `resource_name` property on views or serializers to
specify the `type` key in the json output. It is automatically set for you as the
plural of the view or model name except on resources that do not subclass
`rest_framework.viewsets.ModelViewSet`:
``` python
class Me(generics.GenericAPIView):
    """
    Current user's identity endpoint.

    GET /me
    """
    resource_name = 'users'
    serializer_class = identity_serializers.IdentitySerializer
    allowed_methods = ['GET']
    permission_classes = (permissions.IsAuthenticated, )
```
If you set the `resource_name` property on the object to `False` the data
will be returned without modification.


### Inflecting object keys

This package includes the ability (off by default) to automatically convert json
requests and responses from the python/rest_framework's preferred underscore to
a format of your choice. To hook this up include the following setting in your
project settings:

``` python
JSON_API_FORMAT_KEYS = 'dasherize'
```

Possible values:

* dasherize
* camelize
* underscore
* pluralize

Note: due to the way the inflector works `address_1` can camelize to `address1`
on output but it cannot convert `address1` back to `address_1` on POST or PUT. Keep
this in mind when naming fields with numbers in them.


Example - Without format conversion:
``` js
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
```

Example - With format conversion set to `dasherize`:
``` js
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
```

<!-- 
### Relationships
### Links
### Included
### Errors
### Meta
-->
