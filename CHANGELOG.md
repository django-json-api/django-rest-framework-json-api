# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Note that in line with [Django REST Framework policy](http://www.django-rest-framework.org/topics/release-notes/),
any parts of the framework not mentioned in the documentation should generally be considered private API, and may be subject to change.

## [2.6.0] - 2018-09-20

### Added

* Add testing configuration to `REST_FRAMEWORK` configuration as described in [DRF](https://www.django-rest-framework.org/api-guide/testing/#configuration)
* Add `HyperlinkedRelatedField` and `SerializerMethodHyperlinkedRelatedField`. See [usage docs](docs/usage.md#related-fields)
* Add related urls support. See [usage docs](docs/usage.md#related-urls)
* Add optional [jsonapi-style](http://jsonapi.org/format/) filter backends. See [usage docs](docs/usage.md#filter-backends)

### Deprecated

* Deprecate `MultipleIDMixin` because it doesn't comply with the JSON:API 1.0 spec. Replace it with
  `DjangoFilterBackend` and **change clients** to use `filter[id.in]` query parameter instead of `ids[]`.
  See [usage docs](docs/usage.md#djangofilterbackend). You also have the option to copy the mixin into your code.

### Changed

* Replaced binary `drf_example` sqlite3 db with a [fixture](example/fixtures/drf_example.json). See [getting started](docs/getting-started.md#running-the-example-app).
* Replaced unmaintained [API doc](docs/api.md) with [auto-generated API reference](docs/api.rst).

### Fixed

* Performance improvement when rendering relationships with `ModelSerializer`
* Do not show deprecation warning when user has implemented custom pagination class overwriting default values.


## [2.5.0] - 2018-07-11

### Added

* Add new pagination classes based on JSON:API query parameter *recommendations*:
  * `JsonApiPageNumberPagination` and `JsonApiLimitOffsetPagination`. See [usage docs](docs/usage.md#pagination).
* Add `ReadOnlyModelViewSet` extension with prefetch mixins
* Add support for Django REST Framework 3.8.x
* Introduce `JSON_API_FORMAT_FIELD_NAMES` option replacing `JSON_API_FORMAT_KEYS` but in comparison preserving
  values from being formatted as attributes can contain any [json value](http://jsonapi.org/format/#document-resource-object-attributes).
* Allow overwriting of `get_queryset()` in custom `ResourceRelatedField`

### Deprecated

* Deprecate `PageNumberPagination` and `LimitOffsetPagination`. Use `JsonApiPageNumberPagination` and `JsonApiLimitOffsetPagination` instead.
  * To retain deprecated values for `PageNumberPagination` and `LimitOffsetPagination` create new custom class like the following in your code base:
  ```python
  class CustomPageNumberPagination(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "page_size"

  class CustomLimitOffsetPagination(LimitOffsetPagination):
    max_limit = None
  ```
  and adjust `REST_FRAMEWORK['DEFAULT_PAGINATION_CLASS']` setting accordingly.
* Deprecate `JSON_API_FORMAT_KEYS`, use `JSON_API_FORMAT_FIELD_NAMES`.

### Fixed

* Performance improvement when rendering included data

## [2.4.0] - 2018-01-25

### Added

* Add support for Django REST Framework 3.7.x.
* Add support for Django 2.0.

### Removed

* Drop support for Django 1.8 - 1.10 (EOL)
* Drop support for Django REST Framework < 3.6.3
  (3.6.3 is the first to support Django 1.11)
* Drop support for Python 3.3 (EOL)


## [2.3.0] - 2017-11-28

### Added

* Add support for polymorphic models
* Add nested included serializer support for remapped relations

### Changed

* Enforcing flake8 linting

### Fixed
* When `JSON_API_FORMAT_KEYS` is False (the default) do not translate request
  attributes and relations to snake\_case format. This conversion was unexpected
  and there was no way to turn it off.
* Fix for apps that don't use `django.contrib.contenttypes`.
* Fix `resource_name` support for POST requests and nested serializers

## [2.2.0] - 2017-04-22

### Added

* Add support for Django REST Framework 3.5 and 3.6
* Add support for Django 1.11
* Add support for Python 3.6

## [2.1.1] - 2016-09-26

### Added

* Allow default DRF serializers to operate even when mixed with DRF-JA serializers

### Fixed

* Avoid setting `id` to `None` in the parser simply because it's missing
* Fix out of scope `relation_instance` variable in renderer
* Fix wrong resource type for reverse foreign keys
* Fix documentation typos

## [2.1.0] - 2016-08.18

### Added

* Parse `meta` in JSONParser
* Add code coverage reporting and updated Django versions tested against
* Add support for regular non-ModelSerializers

### Changed

* Documented built in `url` field for generating a `self` link in the `links` key
* Convert `include` field names back to snake_case
* Raise a `ParseError` if an `id` is not included in a PATCH request

### Fixed

* Fix Django 1.10 compatibility
* Performance enhancements to reduce the number of queries in related payloads
* Fix issue where related `SerializerMethodRelatedField` fields were not included even if in `include`
* Fix bug that prevented `fields = ()` in a serializer from being valid
* Fix stale data returned in PATCH to-one relation

## [2.0.1] - 2016-05-02

### Fixed

* Fixes naming error that caused ModelSerializer relationships to fail

## [2.0.0] - 2016-04-29

### Added

* Add `get_related_field_name` for views subclassing RelationshipView to override
* Added LimitOffsetPagination
* Support deeply nested `?includes=foo.bar.baz` without returning intermediate models (bar)
* Allow a view's serializer_class to be fetched at runtime via `get_serializer_class`
* Added support for `get_root_meta` on list serializers

### Changed

* Exception handler can now easily be used on DRF-JA views alongside regular DRF views
* Rename `JSON_API_FORMAT_RELATION_KEYS` to `JSON_API_FORMAT_TYPES` to match what it was actually doing
* Rename `JSON_API_PLURALIZE_RELATION_TYPE` to `JSON_API_PLURALIZE_TYPES`
* Documented ResourceRelatedField and RelationshipView

### Fixed

* Fixes bug where write_only fields still had their keys rendered
