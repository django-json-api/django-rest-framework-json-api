
v2.1.0

* Parse `meta` in JSONParser
* Added code coverage reporting and updated Django versions tested against
* Fixed Django 1.10 compatibility
* Added support for regular non-ModelSerializers
* Added performance enhancements to reduce the number of queries in related payloads
* Fixed bug where related `SerializerMethodRelatedField` fields were not included even if in `include`
* Convert `include` field names back to snake_case
* Documented built in `url` field for generating a `self` link in the `links` key
* Fixed bug that prevented `fields = ()` in a serializer from being valid
* Fixed stale data returned in PATCH to-one relation
* Raise a `ParseError` if an `id` is not included in a PATCH request

v2.0.1

* Fixed naming error that caused ModelSerializer relationships to fail

v2.0.0

* Fixed bug where write_only fields still had their keys rendered
* Exception handler can now easily be used on DRF-JA views alongside regular DRF views
* Added `get_related_field_name` for views subclassing RelationshipView to override
* Renamed `JSON_API_FORMAT_RELATION_KEYS` to `JSON_API_FORMAT_TYPES` to match what it was actually doing
* Renamed `JSON_API_PLURALIZE_RELATION_TYPE` to `JSON_API_PLURALIZE_TYPES`
* Documented ResourceRelatedField and RelationshipView
* Added LimitOffsetPagination
* Support deeply nested `?includes=foo.bar.baz` without returning intermediate models (bar)
* Allow a view's serializer_class to be fetched at runtime via `get_serializer_class`
* Added support for `get_root_meta` on list serializers


v2.0.0-beta.2

* Added JSONAPIMeta class option to models for overriding `resource_name`. #197

