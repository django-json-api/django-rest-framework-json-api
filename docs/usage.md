# Usage

The DJA package implements a custom renderer, parser, exception handler, query filter backends, and
pagination. To get started enable the pieces in `settings.py` that you want to use.

Many features of the [JSON:API](https://jsonapi.org/format) format standard have been implemented using
Mixin classes in `serializers.py`.
The easiest way to make use of those features is to import ModelSerializer variants
from `rest_framework_json_api` instead of the usual `rest_framework`

### Configuration
We suggest that you copy the settings block below and modify it if necessary.
``` python
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
        # If you're performance testing, you will want to use the browseable API
        # without forms, as the forms can generate their own queries.
        # If performance testing, enable:
        # 'example.utils.BrowsableAPIRendererWithoutForms',
        # Otherwise, to play around with the browseable API, enable:
        'rest_framework_json_api.renderers.BrowsableAPIRenderer'
    ),
    'DEFAULT_METADATA_CLASS': 'rest_framework_json_api.metadata.JSONAPIMetadata',
    'DEFAULT_SCHEMA_CLASS': 'rest_framework_json_api.schemas.openapi.AutoSchema',
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
```

### Pagination

DJA pagination is based on [DRF pagination](https://www.django-rest-framework.org/api-guide/pagination/).

When pagination is enabled, the renderer will return a `meta` object with
record count and a `links` object with the next, previous, first, and last links.

Optional query parameters can also be provided to customize the page size or offset limit.

#### Configuring the Pagination Style

Pagination style can be set on a particular viewset with the `pagination_class` attribute or by default for all viewsets
by setting `REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS']` and by setting `REST_FRAMEWORK['PAGE_SIZE']`.

You can configure fixed values for the page size or limit -- or allow the client to choose the size or limit
via query parameters.

Two pagination classes are available:
- `JsonApiPageNumberPagination` breaks a response up into pages that start at a given page number with a given size
  (number of items per page). It can be configured with the following attributes:
  - `page_query_param` (default `page[number]`)
  - `page_size_query_param` (default `page[size]`) Set this to `None` if you don't want to allow the client
     to specify the size.
  - `page_size` (default `REST_FRAMEWORK['PAGE_SIZE']`) default number of items per page unless overridden by
     `page_size_query_param`.
  - `max_page_size` (default `100`) enforces an upper bound on the `page_size_query_param`.
     Set it to `None` if you don't want to enforce an upper bound.

- `JsonApiLimitOffsetPagination` breaks a response up into pages that start from an item's offset in the viewset for
  a given number of items (the limit).
  It can be configured with the following attributes:
  - `offset_query_param` (default `page[offset]`).
  - `limit_query_param` (default `page[limit]`).
  - `default_limit` (default `REST_FRAMEWORK['PAGE_SIZE']`) is the default number of items per page unless
     overridden by `limit_query_param`.
  - `max_limit` (default `100`) enforces an upper bound on the limit.
     Set it to `None` if you don't want to enforce an upper bound.

##### Examples
These examples show how to configure the parameters to use non-standard names and different limits:

```python
from rest_framework_json_api.pagination import JsonApiPageNumberPagination, JsonApiLimitOffsetPagination

class MyPagePagination(JsonApiPageNumberPagination):
    page_query_param = 'page_number'
    page_size_query_param = 'page_length'
    page_size = 3
    max_page_size = 1000

class MyLimitPagination(JsonApiLimitOffsetPagination):
    offset_query_param = 'offset'
    limit_query_param = 'limit'
    default_limit = 3
    max_limit = None
```

### Filter Backends

Following are descriptions of JSON:API-specific filter backends and documentation on suggested usage
for a standard DRF keyword-search filter backend that makes it consistent with JSON:API.

#### QueryParameterValidationFilter

`QueryParameterValidationFilter` validates query parameters to be one of the defined JSON:API query parameters
(sort, include, filter, fields, page) and returns a `400 Bad Request` if a non-matching query parameter
is used. This can help the client identify misspelled query parameters, for example.

If you want to change the list of valid query parameters, override the `.query_regex` attribute:
```python
# compiled regex that matches the allowed https://jsonapi.org/format/#query-parameters
# `sort` and `include` stand alone; `filter`, `fields`, and `page` have []'s
query_regex = re.compile(r"^(sort|include)$|^(?P<type>filter|fields|page)(\[[\w\.\-]+\])?$")
```
For example:
```python
import re
from rest_framework_json_api.filters import QueryParameterValidationFilter

class MyQPValidator(QueryParameterValidationFilter):
    query_regex = re.compile(r"^(sort|include|page|page_size)$|^(?P<type>filter|fields|page)(\[[\w\.\-]+\])?$")
```

If you don't care if non-JSON:API query parameters are allowed (and potentially silently ignored),
simply don't use this filter backend.

#### OrderingFilter

`OrderingFilter` implements the [JSON:API `sort`](https://jsonapi.org/format/#fetching-sorting) and uses
DRF's [ordering filter](https://www.django-rest-framework.org/api-guide/filtering/#orderingfilter).

Per the JSON:API specification, "If the server does not support sorting as specified in the query parameter `sort`,
it **MUST** return `400 Bad Request`." For example, for `?sort=abc,foo,def` where `foo` is a valid
field name and the other two are not valid:
```json
{
    "errors": [
        {
            "detail": "invalid sort parameters: abc,def",
            "source": {
                "pointer": "/data"
            },
            "status": "400"
        }
    ]
}
```

If you want to silently ignore bad sort fields, just use `rest_framework.filters.OrderingFilter` and set
`ordering_param` to `sort`.

#### DjangoFilterBackend

`DjangoFilterBackend` implements a Django ORM-style [JSON:API `filter`](https://jsonapi.org/format/#fetching-filtering)
using the [django-filter](https://django-filter.readthedocs.io/) package.

This filter is not part of the JSON:API standard per-se, other than the requirement
to use the `filter` keyword: It is an optional implementation of a style of
filtering in which each filter is an ORM expression as implemented by
`DjangoFilterBackend` and seems to be in alignment with an interpretation of the
[JSON:API _recommendations_](https://jsonapi.org/recommendations/#filtering), including relationship
chaining.

Filters can be:
- A resource field equality test:
    `?filter[qty]=123`
- Apply other [field lookup](https://docs.djangoproject.com/en/stable/ref/models/querysets/#field-lookups) operators:
    `?filter[name.icontains]=bar` or `?filter[name.isnull]=true`
- Membership in a list of values:
    `?filter[name.in]=abc,123,zzz (name in ['abc','123','zzz'])`
- Filters can be combined for intersection (AND):
    `?filter[qty]=123&filter[name.in]=abc,123,zzz&filter[...]` or
    `?filter[authors.id]=1&filter[authors.id]=2`
- A related resource path can be used:
    `?filter[inventory.item.partNum]=123456` (where `inventory.item` is the relationship path)

The filter returns a `400 Bad Request` error for invalid filter query parameters as in this example
for `GET http://127.0.0.1:8000/nopage-entries?filter[bad]=1`:
```json
{
    "errors": [
        {
            "detail": "invalid filter[bad]",
            "source": {
                "pointer": "/data"
            },
            "status": "400"
        }
    ]
}
```

As this feature depends on `django-filter` you need to run

    pip install djangorestframework-jsonapi['django-filter']

#### SearchFilter

To comply with JSON:API query parameter naming standards, DRF's
[SearchFilter](https://www.django-rest-framework.org/api-guide/filtering/#searchfilter) should
be configured to use a `filter[_something_]` query parameter. This can be done by default by adding the
SearchFilter to `REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS']` and setting `REST_FRAMEWORK['SEARCH_PARAM']` or
adding the `.search_param` attribute to a custom class derived from `SearchFilter`.  If you do this and also
use [`DjangoFilterBackend`](#djangofilterbackend), make sure you set the same values for both classes.


#### Configuring Filter Backends

You can configure the filter backends either by setting the `REST_FRAMEWORK['DEFAULT_FILTER_BACKENDS']` as shown
in the [example settings](#configuration) or individually add them as `.filter_backends` View attributes:

 ```python
from rest_framework_json_api import filters
from rest_framework_json_api import django_filters
from rest_framework import SearchFilter
from models import MyModel

class MyViewset(ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
    filter_backends = (filters.QueryParameterValidationFilter, filters.OrderingFilter,
	                   django_filters.DjangoFilterBackend, SearchFilter)
    filterset_fields = {
        'id': ('exact', 'lt', 'gt', 'gte', 'lte', 'in'),
        'descriptuon': ('icontains', 'iexact', 'contains'),
        'tagline': ('icontains', 'iexact', 'contains'),
    }
    search_fields = ('id', 'description', 'tagline',)

```

### Error objects / Exception handling

For the `exception_handler` class, if the optional `JSON_API_UNIFORM_EXCEPTIONS` is set to True,
all exceptions will respond with the JSON:API [error format](https://jsonapi.org/format/#error-objects).

When `JSON_API_UNIFORM_EXCEPTIONS` is False (the default), non-JSON:API views will respond
with the normal DRF error format.

In case you need a custom error object you can simply raise an `rest_framework.serializers.ValidationError` like the following:

```python
raise serializers.ValidationError(
    {
        "id": "your-id",
        "detail": "your detail message",
        "source": {
            "pointer": "/data/attributes/your-pointer",
        }

    }
)
```

### Performance Testing

If you are trying to see if your viewsets are configured properly to optimize performance,
it is preferable to use `example.utils.BrowsableAPIRendererWithoutForms` instead of the default `BrowsableAPIRenderer`
to remove queries introduced by the forms themselves.

### Serializers

It is recommended to import the base serializer classes from this package
rather than from vanilla DRF. For example,

```python
from rest_framework_json_api import serializers

class MyModelSerializer(serializers.ModelSerializer):
    # ...
```

### Overwriting the resource object's id

Per default the primary key property `pk` on the instance is used as the resource identifier.

It is possible to overwrite the resource id by defining an `id` field on the serializer like:

```python
class UserSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source='email')
    name = serializers.CharField()

    class Meta:
        model = User
```

This also works on generic serializers.

In case you also use a model as a resource related field make sure to overwrite `get_resource_id` by creating a custom `ResourceRelatedField` class:

```python
class UserResourceRelatedField(ResourceRelatedField):
    def get_resource_id(self, value):
        return value.email

class GroupSerializer(serializers.ModelSerializer):
    user = UserResourceRelatedField(queryset=User.objects)
    name = serializers.CharField()

    class Meta:
        model = Group
```

<div class="warning">
    <strong>Note:</strong>
    When using different id than primary key, make sure that your view
    manages it properly by overwriting `get_object`.
</div>

### Setting resource identifier object type

You may manually set resource identifier object type by using `resource_name` property on views, serializers, or
models. In case of setting the `resource_name` property for models you must include the property inside a
`JSONAPIMeta` class on the model. It is usually automatically set for you as the plural of the view or model name except
on resources that do not subclass `rest_framework.viewsets.ModelViewSet`:

Example - `resource_name` on View:
```python
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

Example - `resource_name` on Model:
```python
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

### Build JSON:API view output manually

If in a view you want to build the output manually, you can set `resource_name` to `False`.

Example:
```python
class User(ModelViewSet):
    resource_name = False
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = [{"id": 1, "type": "users", "attributes": {"fullName": "Test User"}}])
```

### Inflecting object and relation keys

This package includes the ability (off by default) to automatically convert [JSON:API field names](https://jsonapi.org/format/#document-resource-object-fields) of requests and responses from the Django REST framework's preferred underscore to a format of your choice. To hook this up include the following setting in your
project settings:

``` python
JSON_API_FORMAT_FIELD_NAMES = 'dasherize'
```

Possible values:

* dasherize
* camelize (first letter is lowercase)
* capitalize (camelize but with first letter uppercase)
* underscore

Note: due to the way the inflector works `address_1` can camelize to `address1`
on output but it cannot convert `address1` back to `address_1` on POST or PATCH. Keep
this in mind when naming fields with numbers in them.


Example - Without format conversion:
``` js
{
    "data": [{
        "type": "identities",
        "id": "3",
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
        "id": "3",
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

A similar option to `JSON_API_FORMAT_FIELD_NAMES` can be set for the types:

``` python
JSON_API_FORMAT_TYPES = 'dasherize'
```

Example without format conversion:

``` js
{
	"data": [{
        "type": "blog_identity",
        "id": "3",
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
        "id": "3",
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
        "id": "3",
        "attributes": {
                ...
        },
        "relationships": {
            "home_towns": {
                "data": [{
                    "type": "home_town",
                    "id": "3"
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
        "id": "3",
        "attributes": {
                ...
        },
        "relationships": {
            "home_towns": {
                "data": [{
                    "type": "home_towns",
                    "id": "3"
                }]
            }
        }
    }]
}
```

#### Related URL segments

Serializer properties in relationship and related resource URLs may be infected using the `JSON_API_FORMAT_RELATED_LINKS` setting.

``` python
JSON_API_FORMAT_RELATED_LINKS = 'dasherize'
```

For example, with a serializer property `created_by` and with `'dasherize'` formatting:

```json
{
  "data": {
      "type": "comments",
      "id": "1",
      "attributes": {
          "text": "Comments are fun!"
      },
      "links": {
          "self": "/comments/1"
      },
      "relationships": {
        "created_by": {
          "links": {
            "self": "/comments/1/relationships/created-by",
            "related": "/comments/1/created-by"
          }
        }
      }
  },
  "links": {
      "self": "/comments/1"
  }
}
```

The relationship name is formatted by the `JSON_API_FORMAT_FIELD_NAMES` setting, but the URL segments are formatted by the `JSON_API_FORMAT_RELATED_LINKS` setting.

<div class="warning">
    <strong>Note:</strong>
    When using this setting make sure that your url pattern matches the formatted url segement.
</div>

### Related fields

#### ResourceRelatedField

Because of the additional structure needed to represent relationships in JSON:API, this package provides the `ResourceRelatedField` for serializers, which
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

In the [JSON:API spec](https://jsonapi.org/format/#document-resource-objects),
relationship objects contain links to related objects. To make this work
on a serializer we need to tell the `ResourceRelatedField` about the
corresponding view. Use the `HyperlinkedModelSerializer` and instantiate
the `ResourceRelatedField` with the relevant keyword arguments:

```python
from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from myapp.models import Order, LineItem, Customer


class OrderSerializer(serializers.HyperlinkedModelSerializer):
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
        related_link_view_name='order-customer-detail',
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
a keyword argument `order_pk`. The
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
        queryset = super().get_queryset()

        # if this viewset is accessed via the 'order-lineitems-list' route,
        # it wll have been passed the `order_pk` kwarg and the queryset
        # needs to be filtered accordingly; if it was accessed via the
        # unnested '/lineitems' route, the queryset should include all LineItems
        order_pk = self.kwargs.get('order_pk')
        if order_pk is not None:
            queryset = queryset.filter(order__pk=order_pk)

        return queryset
```

#### HyperlinkedRelatedField

`relations.HyperlinkedRelatedField` has same functionality as `ResourceRelatedField` but does
not render `data`. Use this in case you only need links of relationships and want to lower payload
and increase performance.

#### SerializerMethodResourceRelatedField

`relations.SerializerMethodResourceRelatedField` combines behaviour of DRF `SerializerMethodField` and 
`ResourceRelatedField`, so it accepts `method_name` together with `model` and links-related arguments.
`data` is rendered in `ResourceRelatedField` manner.

```python
from rest_framework_json_api import serializers
from rest_framework_json_api.relations import SerializerMethodResourceRelatedField

from myapp.models import Order, LineItem


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order

    line_items = SerializerMethodResourceRelatedField(
        model=LineItem,
        many=True,
        method_name='get_big_line_items'
    )

    small_line_items = SerializerMethodResourceRelatedField(
        model=LineItem,
        many=True,
        # default to method_name='get_small_line_items'
    )

    def get_big_line_items(self, instance):
        return LineItem.objects.filter(order=instance).filter(amount__gt=1000)

    def get_small_line_items(self, instance):
        return LineItem.objects.filter(order=instance).filter(amount__lte=1000)

```

or using `related_link_*` with `HyperlinkedModelSerializer`

```python
class OrderSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Order

    line_items = SerializerMethodResourceRelatedField(
        model=LineItem,
        many=True,
        method_name='get_big_line_items',
        related_link_view_name='order-lineitems-list',
        related_link_url_kwarg='order_pk',
    )

    def get_big_line_items(self, instance):
        return LineItem.objects.filter(order=instance).filter(amount__gt=1000)

```


#### Related urls

There is a nice way to handle "related" urls like `/orders/3/lineitems/` or `/orders/3/customer/`.
All you need is just add to `urls.py`:
```python
url(r'^orders/(?P<pk>[^/.]+)/$',
        OrderViewSet.as_view({'get': 'retrieve'}),
        name='order-detail'),
url(r'^orders/(?P<pk>[^/.]+)/(?P<related_field>[-\w]+)/$',
        OrderViewSet.as_view({'get': 'retrieve_related'}),
        name='order-related'),
```
Make sure that RelatedField declaration has `related_link_url_kwarg='pk'` or simply skipped (will be set by default):
```python
    line_items = ResourceRelatedField(
        queryset=LineItem.objects,
        many=True,
        related_link_view_name='order-related',
        related_link_url_kwarg='pk',
        self_link_view_name='order-relationships'
    )

    customer = ResourceRelatedField(
        queryset=Customer.objects,
        related_link_view_name='order-related',
        self_link_view_name='order-relationships'
    )
```
And, the most important part - declare serializer for each related entity:
```python
class OrderSerializer(serializers.HyperlinkedModelSerializer):
    ...
    related_serializers = {
        'customer': 'example.serializers.CustomerSerializer',
        'line_items': 'example.serializers.LineItemSerializer'
    }
```
Or, if you already have `included_serializers` declared and your `related_serializers` look the same, just skip it:
```python
class OrderSerializer(serializers.HyperlinkedModelSerializer):
    ...
    included_serializers = {
        'customer': 'example.serializers.CustomerSerializer',
        'line_items': 'example.serializers.LineItemSerializer'
    }
```

<div class="warning">
    <strong>Note:</strong>
    Even though with related urls relations are served on different urls there are still served
    by the same view. This means that the object permission check is performed on the parent object.
    In other words when the parent object is accessible by the user the related object will be as well.
</div>


### RelationshipView
`rest_framework_json_api.views.RelationshipView` is used to build
relationship views (see the
[JSON:API spec](https://jsonapi.org/format/#fetching-relationships)).
The `self` link on a relationship object should point to the corresponding
relationship view.

The relationship view is fairly simple because it only serializes
[Resource Identifier Objects](https://jsonapi.org/format/#document-resource-identifier-objects)
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
    regex=r'^orders/(?P<pk>[^/.]+)/relationships/(?P<related_field>[-/w]+)$',
    view=OrderRelationshipView.as_view(),
    name='order-relationships'
)
```

The `related_field` kwarg specifies which relationship to use, so
if we are interested in the relationship represented by the related
model field `Order.line_items` on the Order with pk 3, the url would be
`/orders/3/relationships/line_items`. On `HyperlinkedModelSerializer`, the
`ResourceRelatedField` will construct the url based on the provided
`self_link_view_name` keyword argument, which should match the `name=`
provided in the urlconf, and will use the name of the field for the
`related_field` kwarg.
Also we can override `related_field` in the url. Let's say we want the url to be:
`/order/3/relationships/order_items` - all we need to do is just add `field_name_mapping`
dict to the class:
```python
field_name_mapping = {
        'order_items': 'line_items'
    }
```

### Working with polymorphic resources

Polymorphic resources allow you to use specialized subclasses without requiring
special endpoints to expose the specialized versions. For example, if you had a
`Project` that could be either an `ArtProject` or a `ResearchProject`, you can
have both kinds at the same URL.

DJA tests its polymorphic support against [django-polymorphic](https://django-polymorphic.readthedocs.io/en/stable/).
The polymorphic feature should also work with other popular libraries like
django-polymodels or django-typed-models.

As this feature depends on `django-polymorphic` you need to run

    pip install djangorestframework-jsonapi['django-polymorphic']

#### Writing polymorphic resources

A polymorphic endpoint can be set up if associated with a polymorphic serializer.
A polymorphic serializer takes care of (de)serializing the correct instances types and can be defined like this:

```python
class ProjectSerializer(serializers.PolymorphicModelSerializer):
    polymorphic_serializers = [ArtProjectSerializer, ResearchProjectSerializer]

    class Meta:
        model = models.Project
```

It must inherit from `serializers.PolymorphicModelSerializer` and define the `polymorphic_serializers` list.
This attribute defines the accepted resource types.


Polymorphic relations can also be handled with `relations.PolymorphicResourceRelatedField` like this:

```python
class CompanySerializer(serializers.ModelSerializer):
    current_project = relations.PolymorphicResourceRelatedField(
        ProjectSerializer, queryset=models.Project.objects.all())
    future_projects = relations.PolymorphicResourceRelatedField(
        ProjectSerializer, queryset=models.Project.objects.all(), many=True)

    class Meta:
        model = models.Company
```

They must be explicitly declared with the `polymorphic_serializer` (first positional argument) correctly defined.
It must be a subclass of `serializers.PolymorphicModelSerializer`.

<div class="warning">
    <strong>Note:</strong>
    Polymorphic resources are not compatible with
    <code class="docutils literal">
        <span class="pre">resource_name</span>
    </code>
    defined on the view.
</div>

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

To access metadata in incoming requests, the `JSONParser` will add the metadata under a top level `_meta` key in the parsed data dictionary. For instance, to access meta data from a `serializer` object, you may use `serializer.initial_data.get("_meta")`. To customize the `_meta` key, see [here](api.md).

### Links

Adding `url` to `fields` on a serializer will add a `self` link to the `links` key.

Related links will be created automatically when using the Relationship View.

### Included

JSON:API can include additional resources in a single network request.
The specification refers to this feature as
[Compound Documents](https://jsonapi.org/format/#document-compound-documents).
Compound Documents can reduce the number of network requests
which can lead to a better performing web application.
To accomplish this,
the specification permits a top level `included` key.
The list of content within this key are the extra resources
that are related to the primary resource.

To make a Compound Document,
you need to modify your `ModelSerializer`.
`included_serializers` is required to inform DJA of what and how you would like
to include.
`included_resources` tells DJA what you want to include by default.

For example,
suppose you are making an app to go on quests,
and you would like to fetch your chosen knight
along with the quest.
You could accomplish that with:

```python
class KnightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Knight
        fields = ('id', 'name', 'strength', 'dexterity', 'charisma')


class QuestSerializer(serializers.ModelSerializer):
    included_serializers = {
        'knight': KnightSerializer,
    }

    class Meta:
        model = Quest
        fields = ('id', 'title', 'reward', 'knight')

    class JSONAPIMeta:
        included_resources = ['knight']
```

#### Performance improvements

Be aware that using included resources without any form of prefetching **WILL HURT PERFORMANCE** as it will introduce m\*(n+1) queries.

A viewset helper was therefore designed to automatically preload data when possible. Such is automatically available when subclassing `ModelViewSet` or `ReadOnlyModelViewSet`.

It also allows to define custom `select_related` and `prefetch_related` for each requested `include` when needed in special cases:

`rest_framework_json_api.views.ModelViewSet`:
```python
from rest_framework_json_api import views

# When MyViewSet is called with ?include=author it will dynamically prefetch author and author.bio
class MyViewSet(views.ModelViewSet):
    queryset = Book.objects.all()
    select_for_includes = {
        'author': ['author__bio'],
    }
    prefetch_for_includes = {
        '__all__': [],
        'all_authors': [Prefetch('all_authors', queryset=Author.objects.select_related('bio'))],
        'category.section': ['category']
    }
```

An additional convenience DJA class exists for read-only views, just as it does in DRF.
```python
from rest_framework_json_api import views

class MyReadOnlyViewSet(views.ReadOnlyModelViewSet):
    # ...
```

The special keyword `__all__` can be used to specify a prefetch which should be done regardless of the include, similar to making the prefetch yourself on the QuerySet.

Using the helper to prefetch, rather than attempting to minimise queries via `select_related` might give you better performance depending on the characteristics of your data and database.

For example:

If you have a single model, e.g. Book, which has four relations e.g. Author, Publisher, CopyrightHolder, Category.

To display 25 books and related models, you would need to either do:

a) 1 query via selected_related, e.g. SELECT * FROM books LEFT JOIN author LEFT JOIN publisher LEFT JOIN CopyrightHolder LEFT JOIN Category

b) 4 small queries via prefetch_related.

If you have 1M books, 50k authors, 10k categories, 10k copyrightholders
in the `select_related` scenario, you've just created a in-memory table
with 1e18 rows which will likely exhaust any available memory and
slow your database to crawl.

The `prefetch_related` case will issue 4 queries, but they will be small and fast queries.
<!--
### Relationships
### Errors
-->

## Generating an OpenAPI Specification (OAS) 3.0 schema document

DRF has a [OAS schema functionality](https://www.django-rest-framework.org/api-guide/schemas/) to generate an
[OAS 3.0 schema](https://www.openapis.org/) as a YAML or JSON file.

DJA extends DRF's schema support to generate an OAS schema in the JSON:API format.

### AutoSchema Settings

In order to produce an OAS schema that properly represents the JSON:API structure
you have to either add a `schema` attribute to each view class or set the `REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS']`
to DJA's version of AutoSchema.

#### View-based

```python
from rest_framework_json_api.schemas.openapi import AutoSchema

class MyViewset(ModelViewSet):
    schema = AutoSchema
    ...
```

#### Default schema class

```python
REST_FRAMEWORK = {
    # ...
    'DEFAULT_SCHEMA_CLASS': 'rest_framework_json_api.schemas.openapi.AutoSchema',
}
```

### Adding additional OAS schema content

You can extend the OAS schema document by subclassing
[`SchemaGenerator`](https://www.django-rest-framework.org/api-guide/schemas/#schemagenerator)
and extending `get_schema`.


Here's an example that adds OAS `info` and `servers` objects.

```python
from rest_framework_json_api.schemas.openapi import SchemaGenerator as JSONAPISchemaGenerator


class MySchemaGenerator(JSONAPISchemaGenerator):
    """
    Describe my OAS schema info in detail (overriding what DRF put in) and list the servers where it can be found.
    """
    def get_schema(self, request, public):
        schema = super().get_schema(request, public)
        schema['info'] = {
            'version': '1.0',
            'title': 'my demo API',
            'description': 'A demonstration of [OAS 3.0](https://www.openapis.org)',
            'contact': {
                'name': 'my name'
            },
            'license': {
                'name': 'BSD 2 clause',
                'url': 'https://github.com/django-json-api/django-rest-framework-json-api/blob/main/LICENSE',
            }
        }
        schema['servers'] = [
            {'url': 'http://localhost/v1', 'description': 'local docker'},
            {'url': 'http://localhost:8000/v1', 'description': 'local dev'},
            {'url': 'https://api.example.com/v1', 'description': 'demo server'},
            {'url': '{serverURL}', 'description': 'provide your server URL',
             'variables': {'serverURL': {'default': 'http://localhost:8000/v1'}}}
        ]
        return schema
```

### Generate a Static Schema on Command Line

See [DRF documentation for generateschema](https://www.django-rest-framework.org/api-guide/schemas/#generating-a-static-schema-with-the-generateschema-management-command)
To generate a static OAS schema document, using the `generateschema` management command, you **must override DRF's default** `generator_class` with the DJA-specific version:

```text
$ ./manage.py generateschema --generator_class rest_framework_json_api.schemas.openapi.SchemaGenerator
```

You can then use any number of OAS tools such as
[swagger-ui-watcher](https://www.npmjs.com/package/swagger-ui-watcher)
to render the schema:
```text
$ swagger-ui-watcher myschema.yaml
```

Note: Swagger-ui-watcher will complain that "DELETE operations cannot have a requestBody"
but it will still work. This [error](https://github.com/OAI/OpenAPI-Specification/pull/2117)
in the OAS specification will be fixed when [OAS 3.1.0](https://www.openapis.org/blog/2020/06/18/openapi-3-1-0-rc0-its-here)
is published.

([swagger-ui](https://www.npmjs.com/package/swagger-ui) will work silently.)

### Generate a Dynamic Schema in a View

See [DRF documentation for a Dynamic Schema](https://www.django-rest-framework.org/api-guide/schemas/#generating-a-dynamic-schema-with-schemaview).

```python
from rest_framework.schemas import get_schema_view

urlpatterns = [
    ...
    path('openapi', get_schema_view(
        title="Example API",
        description="API for all things …",
        version="1.0.0",
        generator_class=MySchemaGenerator,
    ), name='openapi-schema'),
    path('swagger-ui/', TemplateView.as_view(
        template_name='swagger-ui.html',
        extra_context={'schema_url': 'openapi-schema'}
    ), name='swagger-ui'),
    ...
]
```

## Third Party Packages

### About Third Party Packages

Following the example of [Django REST framework](https://www.django-rest-framework.org/community/third-party-packages/) we also support, encourage and strongly favor the creation of Third Party Packages to encapsulate new behavior rather than adding additional functionality directly to Django REST framework JSON:API especially when it involves adding new dependencies.

We aim to make creating third party packages as easy as possible, whilst keeping a simple and well maintained core API. By promoting third party packages we ensure that the responsibility for a package remains with its author. If a package proves suitably popular it can always be considered for inclusion into the DJA core.

### Existing Third Party Packages

To submit new content, [open an issue](https://github.com/django-json-api/django-rest-framework-json-api/issues/new/choose) or [create a pull request](https://github.com/django-json-api/django-rest-framework-json-api/compare).

* [drf-yasg-json-api](https://github.com/glowka/drf-yasg-json-api) - Automated generation of Swagger/OpenAPI 2.0 from Django REST framework JSON:API endpoints.
