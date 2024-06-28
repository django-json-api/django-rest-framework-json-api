# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Note that in line with [Django REST framework policy](https://www.django-rest-framework.org/topics/release-notes/),
any parts of the framework not mentioned in the documentation should generally be considered private API, and may be subject to change.

## [7.0.2] - 2024-06-28

### Fixed

* Allow overwriting of url field again (regression since 7.0.0)
* Ensured that no fields are rendered when sparse fields is set to an empty value. (regression since 7.0.0)

## [7.0.1] - 2024-06-06

### Added

* Added `429 Too Many Requests` as a possible error response in the OpenAPI schema.

### Fixed

* Ensured that URL and id field are kept when using sparse fields (regression since 7.0.0)

## [7.0.0] - 2024-05-02

### Added

* Added support for Python 3.12
* Added support for Django 5.0
* Added support for Django REST framework 3.15

### Fixed

* Fixed OpenAPI schema generation for `Serializer` when used inside another `Serializer` or as a child of `ListField`.
* `ModelSerializer` fields are now returned in the same order than DRF
* Avoided that an empty attributes dict is rendered in case serializer does not
  provide any attribute fields.
* Avoided shadowing of exception when rendering errors (regression since 4.3.0).
* Ensured that sparse fields only applies when rendering, not when parsing.
* Adjusted that sparse fields properly removes meta fields when not defined.

### Removed

* Removed support for Python 3.7.
* Removed support for Django 3.2.
* Removed support for Django 4.0.
* Removed support for Django 4.1.
* Removed support for Django REST framework 3.13.
* Removed obsolete compat `NullBooleanField` and `get_reference` definitions.

## [6.1.0] - 2023-08-25

This is the last release supporting Python 3.7, Django 3.2, Django 4.0, Django 4.1 and Django REST framework 3.13.

### Added

* Added support for Python 3.11.
* Added support for Django 4.2.
* Added `400 Bad Request` as a possible error response in the OpenAPI schema.

### Changed

* Added support to overwrite serializer methods in customized schema class
* Adjusted some still old formatted strings to f-strings.
* Replaced `OrderedDict` with `dict` which is also ordered since Python 3.7.
* Compound document "include" parameter is only included in the OpenAPI schema if serializer
  implements `included_serializers`.
* Allowed overwriting of resource id by defining an `id` field on the serializer.

    Example:
    ```python
    class CustomIdSerializer(serializers.Serializer):
        id = serializers.CharField(source='name')
        body = serializers.CharField()
    ```

* Allowed overwriting resource id on resource related fields by creating custom `ResourceRelatedField`.

    Example:
    ```python
    class CustomResourceRelatedField(relations.ResourceRelatedField):
        def get_resource_id(self, value):
            return value.name
    ```

* `SerializerMethodResourceRelatedField(many=True)` relationship data now includes a meta section.
* Required relationship fields are now marked as required in the OpenAPI schema.
* Objects in the included array are documented in the OpenAPI schema to possibly have additional
  properties in their "attributes" and "relationships" objects.

### Fixed

* Refactored handling of the `sort` query parameter to fix duplicate declaration in the generated OpenAPI schema definition
* Non-field serializer errors are given a source.pointer value of "/data".
* Fixed "id" field being added to /data/attributes in the OpenAPI schema when it is not rendered there.
* Fixed `SerializerMethodResourceRelatedField(many=True)` fields being given
  a "reltoone" schema reference instead of "reltomany".
* Callable field default values are excluded from the OpenAPI schema, as they don't resolve to YAML data types.

## [6.0.0] - 2022-09-24

### Fixed

* Fixed invalid relationship pointer in error objects when field naming formatting is used.
* Properly resolved related resource type when nested source field is defined.
* Prevented overwriting of pointer in custom error object
* Adhered to field naming format setting when generating schema parameters and required fields.

### Added

* Added support for Django 4.1.
* Added support for Django REST framework 3.14.
* Expanded JSONParser API with `parse_data` method

### Changed

* Improved documentation of how to override DRF's generateschema `--generator_class` to generate a proper DJA OAS schema.

### Removed

* Removed support for Django 2.2.
* Removed support for Django REST framework 3.12.

## [5.0.0] - 2022-01-03

This release is not backwards compatible. For easy migration best upgrade first to version
4.3.0 and resolve all deprecation warnings before updating to 5.0.0

This is the last release supporting Django 2.2 and Django REST framework 3.12.

### Added

* Added support for Django REST framework 3.13.

### Changed

* Adjusted to only use f-strings for slight performance improvement.
* Set minimum required version of inflection to 0.5.
* Set minimum required version of Django Filter to 2.4.
* Set minimum required version of Polymorphic Models for Django to 3.0.
* Set minimum required version of PyYAML to 5.4.

### Removed

* Removed support for Django 3.0.
* Removed support for Django 3.1.
* Removed support for Python 3.6.
* Removed obsolete method `utils.get_included_serializers`.
* Removed optional `format_type` argument of `utils.format_link_segment`.
* Removed `format_type`s default argument of `utils.format_value`. `format_type` is now required.

## [4.3.0] - 2021-12-10

This is the last release supporting Django 3.0, Django 3.1 and Python 3.6.

### Added

* Added support for Django 4.0.
* Added support for Python 3.10.

### Fixed

* Adjusted error messages to correctly use capital "JSON:API" abbreviation as used in the specification.
* Avoid error when `parser_context` is `None` while parsing.
* Raise comprehensible error when reserved field names `meta` and `results` are used.
* Use `relationships` in the error object `pointer` when the field is actually a relationship.
* Added missing inflection to the generated OpenAPI schema.
* Added missing error message when `resource_name` is not properly configured.

### Changed

* Moved resolving of `included_serialzers` and `related_serializers` classes to serializer's meta class.

### Deprecated

* Deprecated `get_included_serializers(serializer)` function under `rest_framework_json_api.utils`. Use `serializer.included_serializers` instead.
* Deprecated support for field name `type` as it may not be used according to the [JSON:API spec](https://jsonapi.org/format/#document-resource-object-fields).

## [4.2.1] - 2021-07-06

### Fixed

* Included `PreloadIncludesMixin` in `ReadOnlyModelViewSet` to enable the usage of [performance utilities](https://django-rest-framework-json-api.readthedocs.io/en/stable/usage.html#performance-improvements) on read only views (regression since 2.8.0)
* Removed invalid validation of default `included_resources` (regression since 4.2.0)

## [4.2.0] - 2021-05-12

### Added

* Added support for Django 3.2.
* Added support for tags in OAS schema

### Fixed

* Allow `get_serializer_class` to be overwritten when using related urls without defining `serializer_class` fallback
* Preserve field names when no formatting is configured.
* Properly support `JSON_API_FORMAT_RELATED_LINKS` setting in related urls. In case you want to use `dasherize` for formatting links make sure that your url pattern matches dashes as well like following example:
  ```
  url(r'^orders/(?P<pk>[^/.]+)/(?P<related_field>[-\w]+)/$',
      OrderViewSet.as_view({'get': 'retrieve_related'}),
      name='order-related'),
  ```
* Ensure default `included_resources` are considered when calculating prefetches.
* Avoided error when using `include` query parameter on related urls (a regression since 4.1.0)

### Deprecated

* Deprecated default `format_type` argument of `rest_framework_json_api.utils.format_value`. Use `rest_framework_json_api.utils.format_field_name` or specify specifc `format_type` instead.
* Deprecated `format_type` argument of `rest_framework_json_api.utils.format_link_segment`. Use `rest_framework_json_api.utils.format_value` instead.

## [4.1.0] - 2021-03-08

### Added

* Ability for the user to select `included_serializers` to apply when using `BrowsableAPI`, based on available `included_serializers` defined for the current endpoint.
* Ability for the user to format serializer properties in URL segments using the `JSON_API_FORMAT_RELATED_LINKS` setting.

### Fixed

* Allow users to overwrite a view's `get_serializer_class()` method when using [related urls](https://django-rest-framework-json-api.readthedocs.io/en/stable/usage.html#related-urls)
* Correctly resolve the resource type of `ResourceRelatedField(many=True)` fields on plain serializers
* Render `meta_fields` in included resources


## [4.0.0] - 2020-10-31

This release is not backwards compatible. For easy migration best upgrade first to version
3.2.0 and resolve all deprecation warnings before updating to 4.0.0

### Added

* Added support for Django REST framework 3.12.
* Added support for Django 3.1.
* Added support for Python 3.9.
* Added initial optional support for [openapi](https://www.openapis.org/) schema generation. Enable with:
  ```
  pip install djangorestframework-jsonapi['openapi']
  ```
  This first release is a start at implementing OAS schema generation. To use the generated schema you may
  still need to manually add some schema attributes but can expect future improvements here and as
  upstream DRF's OAS schema generation continues to mature.

### Removed


* Removed support for Python 3.5.
* Removed support for Django 1.11.
* Removed support for Django 2.1.
* Removed support for Django REST framework 3.10 and 3.11.
* Removed obsolete `source` argument of `SerializerMethodResourceRelatedField`.
* Removed obsolete setting `JSON_API_SERIALIZE_NESTED_SERIALIZERS_AS_ATTRIBUTE` to render nested serializers as relationships.
  Default is render as attribute now.

### Fixed

* Stopped `SparseFieldsetsMixin` interpretting invalid fields query parameter (e.g. invalidfields[entries]=blog,headline).

## [3.2.0] - 2020-08-26

This is the last release supporting Django 1.11, Django 2.1, Django REST framework 3.10, Django REST framework 3.11 and Python 3.5.

### Added

* Added support for serializing nested serializers as attribute json value introducing setting `JSON_API_SERIALIZE_NESTED_SERIALIZERS_AS_ATTRIBUTE`
 * Note: As keys of nested serializers are not JSON:API spec field names they are not inflected by format field names option.
* Added `rest_framework_json_api.serializer.Serializer` class to support initial JSON:API views without models.
  * Note that serializers derived from this class need to define `resource_name` in their `Meta` class.
  * This fix might be a **BREAKING CHANGE** if you use `rest_framework_json_api.serializers.Serializer` for non JSON:API spec views (usually `APIView`). You need to change those serializers classes to use `rest_framework.serializers.Serializer` instead.

### Fixed

* Avoid `AttributeError` for PUT and PATCH methods when using `APIView`
* Clear many-to-many relationships instead of deleting related objects during PATCH on `RelationshipView`
* Allow POST, PATCH, DELETE for actions in `ReadOnlyModelViewSet`. Regression since version `2.8.0`.
* Properly format nested errors

### Changed

* `SerializerMethodResourceRelatedField` is now consistent with DRF `SerializerMethodField`:
   * Pass `method_name` argument to specify method name. If no value is provided, it defaults to `get_{field_name}`
* Allowed repeated filter query parameters.

### Deprecated

* Deprecate `source` argument of `SerializerMethodResourceRelatedField`, use `method_name` instead
* Rendering nested serializers as relationships is deprecated. Use `ResourceRelatedField` instead


## [3.1.0] - 2020-02-08

### Added

* Added support for Python 3.8
* Added support for Django REST framework 3.11
* Added support for Django 3.0

### Fixed

* Ensured that `409 Conflict` is returned when processing a `PATCH` request in which the resource object’s type and id do not match the server’s endpoint as outlined in [JSON:API](https://jsonapi.org/format/#crud-updating-responses-409) spec.
* Properly return parser error when primary data is of invalid type
* Pass instance to child serializers when using `PolymorphicModelSerializer`
* Properly resolve related resource type when using `PolymorphicModelSerializer`

## [3.0.0] - 2019-10-14

This release is not backwards compatible. For easy migration best upgrade first to version
2.8.0 and resolve all deprecation warnings before updating to 3.0.0

### Added

* Added support for Django REST framework 3.10.
* Added code from `ErrorDetail` into the JSON:API error object.

### Changed

* Moved dependency definition for `django-polymorphic` and `django-filter` into extra requires.
  Hence dependencies of each optional module can be installed with pip using
  ```
  pip install djangorestframework-jsonapi['django-polymorphic']
  pip install djangorestframework-jsonapi['django-filter']
  ```

### Removed

* Removed support for Python 2.7 and 3.4.
* Removed support for Django Filter 1.1.
* Removed obsolete dependency six.
* Removed support for Django REST framework <=3.9.
* Removed support for Django 2.0.
* Removed obsolete mixins `MultipleIDMixin` and `PrefetchForIncludesHelperMixin`
* Removed obsolete settings `JSON_API_FORMAT_KEYS`, `JSON_API_FORMAT_RELATION_KEYS` and
  `JSON_API_PLURALIZE_RELATION_TYPE`
* Removed obsolete util methods `format_keys` and `format_relation_name`
* Removed obsolete pagination classes `PageNumberPagination` and `LimitOffsetPagination`

### Fixed

* Avoid printing invalid pointer when api returns 404.
* Avoid exception when using `ResourceIdentifierObjectSerializer` with unexisting primary key.
* Format metadata field names correctly for OPTIONS request.


## [2.8.0] - 2019-06-13

This is the last release supporting Python 2.7, Python 3.4, Django Filter 1.1, Django REST framework <=3.9 and Django 2.0.

### Added

* Add support for Django 2.2

### Changed

* Allow to define `select_related` per include using [select_for_includes](https://django-rest-framework-json-api.readthedocs.io/en/stable/usage.html#performance-improvements)
* Use REST framework serializer functionality to extract includes. This adds support like using
  dotted notations in source attribute in `ResourceRelatedField`.

### Fixed

* Avoid exception when trying to include skipped relationship
* Don't swallow `filter[]` params when there are several
* Fix DeprecationWarning regarding collections.abc import in Python 3.7
* Allow OPTIONS request to be used on RelationshipView
* Remove non-JSON:API methods (PUT and TRACE) from ModelViewSet and RelationshipView.
  This fix might be a **BREAKING CHANGE** if your clients are incorrectly using PUT instead of PATCH.
* Avoid validation error for missing fields on a PATCH request using polymorphic serializers

### Deprecated

* Deprecate `PrefetchForIncludesHelperMixin` use `PreloadIncludesMixin` instead

## [2.7.0] - 2019-01-14

### Added

* Add support for Django 2.1, DRF 3.9 and Python 3.7. Please note:
  - Django >= 2.1 is not supported with Python < 3.5.

### Fixed

* Pass context from `PolymorphicModelSerializer` to child serializers to support fields which require a `request` context such as `url`.
* Avoid patch on `RelationshipView` deleting relationship instance when constraint would allow null ([#242](https://github.com/django-json-api/django-rest-framework-json-api/issues/242))
* Avoid error with related urls when retrieving relationship which is referenced as `ForeignKey` on parent
* Do not render `write_only` relations
* Do not skip empty one-to-one relationships
* Allow `HyperlinkRelatedField` to be used with [related urls](https://django-rest-framework-json-api.readthedocs.io/en/stable/usage.html?highlight=related%20links#related-urls)
* Avoid exception in `AutoPrefetchMixin` when including a reverse one to one relation ([#537](https://github.com/django-json-api/django-rest-framework-json-api/issues/537))
* Avoid requested resource(s) to be added to included as well ([#524](https://github.com/django-json-api/django-rest-framework-json-api/issues/524))

## [2.6.0] - 2018-09-20

### Added

* Add testing configuration to `REST_FRAMEWORK` configuration as described in [DRF](https://www.django-rest-framework.org/api-guide/testing/#configuration)
* Add `HyperlinkedRelatedField` and `SerializerMethodHyperlinkedRelatedField`. See [usage docs](docs/usage.md#related-fields)
* Add related urls support. See [usage docs](docs/usage.md#related-urls)
* Add optional [jsonapi-style](https://jsonapi.org/format/) filter backends. See [usage docs](docs/usage.md#filter-backends)

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
* Add support for Django REST framework 3.8.x
* Introduce `JSON_API_FORMAT_FIELD_NAMES` option replacing `JSON_API_FORMAT_KEYS` but in comparison preserving
  values from being formatted as attributes can contain any [json value](https://jsonapi.org/format/#document-resource-object-attributes).
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

* Add support for Django REST framework 3.7.x.
* Add support for Django 2.0.

### Removed

* Drop support for Django 1.8 - 1.10 (EOL)
* Drop support for Django REST framework < 3.6.3
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

* Add support for Django REST framework 3.5 and 3.6
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
