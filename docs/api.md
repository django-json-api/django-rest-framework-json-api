
# API

## mixins
### MultipleIDMixin

Add this mixin to a view to override `get_queryset` to automatically filter
records by `ids[]=1&ids[]=2` in URL query params.

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
