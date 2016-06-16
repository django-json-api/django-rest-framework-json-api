
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

### Serializers

It is recommended to import the base serializer classes from this package
rather than from vanilla DRF. For example,

```python
from rest_framework_json_api import serializers

class MyModelSerializer(serializers.ModelSerializers):
    # ...
```

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
`resource_name` specified on a serializer or model). Setting the `resource_name`
on the view should be used sparingly as serializers and models are shared between
multiple endpoints. Setting the `resource_name` on views may result in a different
`type` being set depending on which endpoint the resource is fetched from.


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

#### Types

A similar option to JSON\_API\_FORMAT\_KEYS can be set for the types:

``` python
JSON_API_FORMAT_TYPES = 'dasherize'
```

Example without format conversion:

``` js
{
	"data": [{
        "type": "blog_identity",
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
        "type": "blog-identity",
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
JSON_API_PLURALIZE_TYPES = True
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

### Related fields

Because of the additional structure needed to represent relationships in JSON
API, this package provides the `ResourceRelatedField` for serializers, which
works similarly to `PrimaryKeyRelatedField`. By default,
`rest_framework_json_api.serializers.ModelSerializer` will use this for
related fields automatically. It can be instantiated explicitly as in the
following example:

```python
from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from myapp.models import Order, LineItem, Customer


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order

    line_items = ResourceRelatedField(
        queryset=LineItem.objects,
        many=True  # necessary for M2M fields & reverse FK fields
    )

    customer = ResourceRelatedField(
        queryset=Customer.objects  # queryset argument is required
    )                              # except when read_only=True

```

In the [JSON API spec](http://jsonapi.org/format/#document-resource-objects),
relationship objects contain links to related objects. To make this work
on a serializer we need to tell the `ResourceRelatedField` about the
corresponding view. Use the `HyperlinkedModelSerializer` and instantiate
the `ResourceRelatedField` with the relevant keyword arguments:

```python
from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from myapp.models import Order, LineItem, Customer


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order

    line_items = ResourceRelatedField(
        queryset=LineItem.objects,
        many=True,
        related_link_view_name='order-lineitems-list',
        related_link_url_kwarg='order_pk',
        self_link_view_name='order_relationships'
    )

    customer = ResourceRelatedField(
        queryset=Customer.objects,
        related_link_view-name='order-customer-detail',
        related_link_url_kwarg='order_pk',
        self_link_view_name='order-relationships'
    )
```

* `related_link_view_name` is the name of the route for the related
view.

* `related_link_url_kwarg` is the keyword argument that will be passed
to the view that identifies the 'parent' object, so that the results
can be filtered to show only those objects related to the 'parent'.

* `self_link_view_name` is the name of the route for the `RelationshipView`
(see below).

In this example, `reverse('order-lineitems-list', kwargs={'order_pk': 3}`
should resolve to something like `/orders/3/lineitems`, and that route
should instantiate a view or viewset for `LineItem` objects that accepts
a keword argument `order_pk`. The
[drf-nested-routers](https://github.com/alanjds/drf-nested-routers) package
is useful for defining such nested routes in your urlconf.

The corresponding viewset for the `line-items-list` route in the above example
might look like the following. Note that in the typical use case this would be
the same viewset used for the `/lineitems` endpoints; when accessed through
the nested route `/orders/<order_pk>/lineitems` the queryset is filtered using
the `order_pk` keyword argument to include only the lineitems related to the
specified order.

```python
from rest_framework import viewsets

from myapp.models import LineItem
from myapp.serializers import LineItemSerializer


class LineItemViewSet(viewsets.ModelViewSet):
    queryset = LineItem.objects
    serializer_class = LineItemSerializer

    def get_queryset(self):
        queryset = self.queryset

        # if this viewset is accessed via the 'order-lineitems-list' route,
        # it wll have been passed the `order_pk` kwarg and the queryset
        # needs to be filtered accordingly; if it was accessed via the
        # unnested '/lineitems' route, the queryset should include all LineItems
        if 'order_pk' in self.kwargs:
            order_pk = self.kwargs['order_pk']
            queryset = queryset.filter(order__pk=order_pk])

        return queryset
```

### RelationshipView
`rest_framework_json_api.views.RelationshipView` is used to build
relationship views (see the 
[JSON API spec](http://jsonapi.org/format/#fetching-relationships)).
The `self` link on a relationship object should point to the corresponding
relationship view.

The relationship view is fairly simple because it only serializes
[Resource Identifier Objects](http://jsonapi.org/format/#document-resource-identifier-objects)
rather than full resource objects. In most cases the following is sufficient:

```python
from rest_framework_json_api.views import RelationshipView

from myapp.models import Order


class OrderRelationshipView(RelationshipView):
    queryset = Order.objects

```

The urlconf would need to contain a route like the following:

```python
url(
    regex=r'^orders/(?P<pk>[^/.]+/relationships/(?P<related_field>[^/.]+)$',
    view=OrderRelationshipView.as_view(),
    name='order-relationships'
)
```

The `related_field` kwarg specifies which relationship to use, so
if we are interested in the relationship represented by the related
model field `Order.line_items` on the Order with pk 3, the url would be
`/order/3/relationships/line_items`. On `HyperlinkedModelSerializer`, the
`ResourceRelatedField` will construct the url based on the provided
`self_link_view_name` keyword argument, which should match the `name=`
provided in the urlconf, and will use the name of the field for the
`related_field` kwarg.
Also we can override `related_field` in the url. Let's say we want the url to be:
`/order/3/relationships/order_items` - all we need to do is just add `field_name_mapping`
dict to the class:
```python
field_name_mapping = {
        'line_items': 'order_items'
    }
```


### Meta

You may add metadata to the rendered json in two different ways: `meta_fields` and `get_root_meta`.

On any `rest_framework_json_api.serializers.ModelSerializer` you may add a `meta_fields`
property to the `Meta` class. This behaves in the same manner as the default
`fields` property and will cause `SerializerMethodFields` or model values to be
added to the `meta` object within the same `data` as the serializer.

To add metadata to the top level `meta` object add:

``` python
def get_root_meta(self, resource, many):
    if many:
      # Dealing with a list request
      return {
          'size': len(resource)
      }
    else:
      # Dealing with a detail request
      return {
        'foo': 'bar'
      }
```
to the serializer. It must return a dict and will be merged with the existing top level `meta`.

### Links

Adding `url` to `fields` on a serializer will add a `self` link to the `links` key.

Related links will be created automatically when using the Relationship View.

<!--
### Relationships
### Included
### Errors
-->
