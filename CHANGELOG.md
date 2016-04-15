
v2.0.0

* Renamed `JSON_API_FORMAT_RELATION_KEYS` to `JSON_API_FORMAT_TYPES` to match what it was actually doing
* Renamed `JSON_API_PLURALIZE_RELATION_TYPE` to `JSON_API_PLURALIZE_TYPES`
* Documented ResourceRelatedField and RelationshipView
* Added LimitOffsetPagination
* Support deeply nested `?includes=foo.bar.baz` without returning intermediate models (bar)
* Allow a view's serializer_class to be fetched at runtime via `get_serializer_class`
* Added support for `get_root_meta` on list serializers


v2.0.0-beta.2

* Added JSONAPIMeta class option to models for overriding `resource_name`. #197

