
# API

## mixins
### MultipleIDMixin

Add this mixin to a view to override `get_queryset` to filter
records by `ids[]=1&ids[]=2` in URL query params.

For example:
```http request
GET /widgets/?ids[]=123&ids[]=456
```

You might want to consider using the `FilterMixin` where the equivalent example is:
```http request
GET /widgets/?filter[id]=123,456
```

### FilterMixin

This ViewSet mixin augments `get_queryset` to provide JSON API filter query parameter support
per the [recommendation](http://jsonapi.org/recommendations/#filtering).

The `filter` syntax is `filter[name1]=list,of,alternative,values&filter[name2]=more,alternatives...`
which can be interpreted as `(name1 in [list,of,alternative,values]) and (name2 in [more,alternatives])`
`name` can be `id` or attributes fields.

For example:

```http request
GET /widgets/?filter[name]=can+opener,tap&filter[color]=red
```

### SortMixin

This ViewSet mixin augments `get_queryset` to provide JSON API sort query parameter support
per the [recommendation](http://jsonapi.org/format/#fetching-sorting).

The `sort` syntax is `sort=-field1,field2,...`

For example:

```http request
GET /widgets/?sort=-name,color
```

### SparseFieldsetsMixin

This Serializer mixin implements [sparse fieldsets](http://jsonapi.org/format/#fetching-sparse-fieldsets)
with the `fields[type]=` parameter. It is included by default in the HyperLinkedModelSerializer and
ModelSerializer classes.

For example:

```http request
GET /widgets/?fields[widgets]=name
``` 

### IncludedResourcesValidationMixin

This Serializer mixin implements [included compound documents](http://jsonapi.org/format/#document-compound-documents)
with the `include=` parameter. It is included by default in the HyperLinkedModelSerializer and
ModelSerializer classes. 

For example:

```http request
GET /widgets/?included=locations
```

## rest_framework_json_api.renderers.JSONRenderer

The `JSONRenderer` exposes a number of methods that you may override if you need
highly custom rendering control.

#### extract_attributes

`extract_attributes(fields, resource)`

Builds the `attributes` object of the JSON API resource object.

#### extract_relationships

`extract_relationships(fields, resource, resource_instance)`

Builds the `relationships` top level object based on related serializers.

#### extract_included

`extract_included(fields, resource, resource_instance, included_resources)`

Adds related data to the top level `included` key when the request includes `?include=example,example_field2`

#### extract_meta

`extract_meta(serializer, resource)`

Gathers the data from serializer fields specified in `meta_fields` and adds it to the `meta` object.

#### extract_root_meta

`extract_root_meta(serializer, resource)`

Calls a `get_root_meta` function on a serializer, if it exists.

#### build_json_resource_obj

`build_json_resource_obj(fields, resource, resource_instance, resource_name)`

Builds the resource object (type, id, attributes) and extracts relationships.

## rest_framework_json_api.parsers.JSONParser

Similar to `JSONRenderer`, the `JSONParser` you may override the following methods if you need
highly custom parsing control.

#### parse_metadata

`parse_metadata(result)`

Returns a dictionary which will be merged into parsed data of the request. By default, it reads the `meta` content in the request body and returns it in a dictionary with a `_meta` top level key.
