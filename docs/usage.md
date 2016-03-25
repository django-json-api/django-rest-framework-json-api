
# Usage

The DJA package implements a custom renderer, parser, exception handler, and
pagination. To get started enable the pieces in `settings.py` that you want to use.

Many features of the JSON:API format standard have been implemented using Mixin classes in `serializers.py`.
The easiest way to make use of those features is to import ModelSerializer variants
from `rest_framework_json_api` instead of the usual `rest_framework`

### Configuration
We suggest that you copy the settings block below and modify it if necessary.
``` python
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
```

If `PAGE_SIZE` is set the renderer will return a `meta` object with
record count and a `links` object with the next, previous, first, and last links.
Pages can be selected with the `page` GET parameter. Page size can be controlled
per request via the `PAGINATE_BY_PARAM` query parameter (`page_size` by default).

### Setting the resource_name

You may manually set the `resource_name` property on views, serializers, or
models to specify the `type` key in the json output. In the case of setting the
`resource_name` property for models you must include the property inside a
`JSONAPIMeta` class on the model. It is automatically set for you as the plural
of the view or model name except on resources that do not subclass
`rest_framework.viewsets.ModelViewSet`:


Example - `resource_name` on View:
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


Example - `resource_name` on Model:
``` python
class Me(models.Model):
    """
    A simple model
    """
    name = models.CharField(max_length=100)

    class JSONAPIMeta:
        resource_name = "users"
```
If you set the `resource_name` on a combination of model, serializer, or view
in the same hierarchy, the name will be resolved as following: view >
serializer > model. (Ex: A view `resource_name` will always override a
`resource_name` specified on a serializer or model)


### Inflecting object and relation keys

This package includes the ability (off by default) to automatically convert json
requests and responses from the python/rest_framework's preferred underscore to
a format of your choice. To hook this up include the following setting in your
project settings:

``` python
JSON_API_FORMAT_KEYS = 'dasherize'
```

Possible values:

* dasherize
* camelize (first letter is lowercase)
* capitalize (camelize but with first letter uppercase)
* underscore

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

#### Relationship types

A similar option to JSON\_API\_FORMAT\_RELATION\_KEYS can be set for the relationship names:

``` python
JSON_API_FORMAT_RELATION_KEYS = 'dasherize'
```

Example without format conversion:

``` js
{
	"data": [{
        "type": "identities",
        "id": 3,
        "attributes": {
                ...
        },
        "relationships": {
            "home_town": {
                "data": [{
                    "type": "home_town",
                    "id": 3
                }]
            }
        }
    }]
}
```

When set to dasherize:


``` js
{
	"data": [{
        "type": "identities",
        "id": 3,
        "attributes": {
                ...
        },
        "relationships": {
            "home_town": {
                "data": [{
                    "type": "home-town",
                    "id": 3
                }]
            }
        }
    }]
}
```
It is also possible to pluralize the types like so:

```python
JSON_API_PLURALIZE_RELATION_TYPE = True
```
Example without pluralization:

``` js
{
	"data": [{
        "type": "identity",
        "id": 3,
        "attributes": {
                ...
        },
        "relationships": {
            "home_towns": {
                "data": [{
                    "type": "home_town",
                    "id": 3
                }]
            }
        }
    }]
}
```

When set to pluralize:


``` js
{
	"data": [{
        "type": "identities",
        "id": 3,
        "attributes": {
                ...
        },
        "relationships": {
            "home_towns": {
                "data": [{
                    "type": "home_towns",
                    "id": 3
                }]
            }
        }
    }]
}
```

Both `JSON_API_PLURALIZE_RELATION_TYPE` and `JSON_API_FORMAT_RELATION_KEYS` can be combined to
achieve different results.

### Meta

You may add metadata to the rendered json in two different ways: `meta_fields` and `get_root_meta`.

On any `rest_framework_json_api.serializers.ModelSerializer` you may add a `meta_fields`
property to the `Meta` class. This behaves in the same manner as the default
`fields` property and will cause `SerializerMethodFields` or model values to be
added to the `meta` object within the same `data` as the serializer.

To add metadata to the top level `meta` object add:

``` python
def get_root_meta(self, obj):
    return {
        'size': len(obj)
    }
```
to the serializer. It must return a dict and will be merged with the existing top level `meta`.

<!--
### Relationships
### Links
### Included
### Errors
-->
