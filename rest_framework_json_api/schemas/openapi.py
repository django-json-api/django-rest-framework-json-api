import warnings
from urllib.parse import urljoin

from rest_framework.fields import empty
from rest_framework.relations import ManyRelatedField
from rest_framework.schemas import openapi as drf_openapi
from rest_framework.schemas.utils import is_list_view

from rest_framework_json_api import serializers, views
from rest_framework_json_api.compat import get_reference
from rest_framework_json_api.relations import ManySerializerMethodResourceRelatedField
from rest_framework_json_api.utils import format_field_name


class SchemaGenerator(drf_openapi.SchemaGenerator):
    """
    Extend DRF's SchemaGenerator to implement JSON:API flavored generateschema command.
    """

    #: These JSON:API component definitions are referenced by the generated OAS schema.
    #: If you need to add more or change these static component definitions, extend this dict.
    jsonapi_components = {
        "schemas": {
            "jsonapi": {
                "type": "object",
                "description": "The server's implementation",
                "properties": {
                    "version": {"type": "string"},
                    "meta": {"$ref": "#/components/schemas/meta"},
                },
                "additionalProperties": False,
            },
            "resource": {
                "type": "object",
                "required": ["type", "id"],
                "additionalProperties": False,
                "properties": {
                    "type": {"$ref": "#/components/schemas/type"},
                    "id": {"$ref": "#/components/schemas/id"},
                    "attributes": {
                        "type": "object",
                        # ...
                    },
                    "relationships": {
                        "type": "object",
                        # ...
                    },
                    "links": {"$ref": "#/components/schemas/links"},
                    "meta": {"$ref": "#/components/schemas/meta"},
                },
            },
            "include": {
                "type": "object",
                "required": ["type", "id"],
                "additionalProperties": False,
                "properties": {
                    "type": {"$ref": "#/components/schemas/type"},
                    "id": {"$ref": "#/components/schemas/id"},
                    "attributes": {
                        "type": "object",
                        "additionalProperties": True,
                        # ...
                    },
                    "relationships": {
                        "type": "object",
                        "additionalProperties": True,
                        # ...
                    },
                    "links": {"$ref": "#/components/schemas/links"},
                    "meta": {"$ref": "#/components/schemas/meta"},
                },
            },
            "link": {
                "oneOf": [
                    {
                        "description": "a string containing the link's URL",
                        "type": "string",
                        "format": "uri-reference",
                    },
                    {
                        "type": "object",
                        "required": ["href"],
                        "properties": {
                            "href": {
                                "description": "a string containing the link's URL",
                                "type": "string",
                                "format": "uri-reference",
                            },
                            "meta": {"$ref": "#/components/schemas/meta"},
                        },
                    },
                ]
            },
            "links": {
                "type": "object",
                "additionalProperties": {"$ref": "#/components/schemas/link"},
            },
            "reltoone": {
                "description": "a singular 'to-one' relationship",
                "type": "object",
                "properties": {
                    "links": {"$ref": "#/components/schemas/relationshipLinks"},
                    "data": {"$ref": "#/components/schemas/relationshipToOne"},
                    "meta": {"$ref": "#/components/schemas/meta"},
                },
            },
            "relationshipToOne": {
                "description": "reference to other resource in a to-one relationship",
                "anyOf": [
                    {"$ref": "#/components/schemas/nulltype"},
                    {"$ref": "#/components/schemas/linkage"},
                ],
            },
            "reltomany": {
                "description": "a multiple 'to-many' relationship",
                "type": "object",
                "properties": {
                    "links": {"$ref": "#/components/schemas/relationshipLinks"},
                    "data": {"$ref": "#/components/schemas/relationshipToMany"},
                    "meta": {"$ref": "#/components/schemas/meta"},
                },
            },
            "relationshipLinks": {
                "description": "optional references to other resource objects",
                "type": "object",
                "additionalProperties": True,
                "properties": {
                    "self": {"$ref": "#/components/schemas/link"},
                    "related": {"$ref": "#/components/schemas/link"},
                },
            },
            "relationshipToMany": {
                "description": "An array of objects each containing the "
                "'type' and 'id' for to-many relationships",
                "type": "array",
                "items": {"$ref": "#/components/schemas/linkage"},
                "uniqueItems": True,
            },
            # A RelationshipView uses a ResourceIdentifierObjectSerializer (hence the name
            # ResourceIdentifierObject returned by get_component_name()) which serializes type
            # and id. These can be lists or individual items depending on whether the
            # relationship is toMany or toOne so offer both options since we are not iterating
            # over all the possible {related_field}'s but rather rendering one path schema
            # which may represent toMany and toOne relationships.
            "ResourceIdentifierObject": {
                "oneOf": [
                    {"$ref": "#/components/schemas/relationshipToOne"},
                    {"$ref": "#/components/schemas/relationshipToMany"},
                ]
            },
            "linkage": {
                "type": "object",
                "description": "the 'type' and 'id'",
                "required": ["type", "id"],
                "properties": {
                    "type": {"$ref": "#/components/schemas/type"},
                    "id": {"$ref": "#/components/schemas/id"},
                    "meta": {"$ref": "#/components/schemas/meta"},
                },
            },
            "pagination": {
                "type": "object",
                "properties": {
                    "first": {"$ref": "#/components/schemas/pageref"},
                    "last": {"$ref": "#/components/schemas/pageref"},
                    "prev": {"$ref": "#/components/schemas/pageref"},
                    "next": {"$ref": "#/components/schemas/pageref"},
                },
            },
            "pageref": {
                "oneOf": [
                    {"type": "string", "format": "uri-reference"},
                    {"$ref": "#/components/schemas/nulltype"},
                ]
            },
            "failure": {
                "type": "object",
                "required": ["errors"],
                "properties": {
                    "errors": {"$ref": "#/components/schemas/errors"},
                    "meta": {"$ref": "#/components/schemas/meta"},
                    "jsonapi": {"$ref": "#/components/schemas/jsonapi"},
                    "links": {"$ref": "#/components/schemas/links"},
                },
            },
            "errors": {
                "type": "array",
                "items": {"$ref": "#/components/schemas/error"},
                "uniqueItems": True,
            },
            "error": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "status": {"type": "string"},
                    "links": {"$ref": "#/components/schemas/links"},
                    "code": {"type": "string"},
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                    "source": {
                        "type": "object",
                        "properties": {
                            "pointer": {
                                "type": "string",
                                "description": (
                                    "A [JSON Pointer](https://tools.ietf.org/html/rfc6901) "
                                    "to the associated entity in the request document "
                                    "[e.g. `/data` for a primary data object, or "
                                    "`/data/attributes/title` for a specific attribute."
                                ),
                            },
                            "parameter": {
                                "type": "string",
                                "description": "A string indicating which query parameter "
                                "caused the error.",
                            },
                            "meta": {"$ref": "#/components/schemas/meta"},
                        },
                    },
                },
            },
            "onlymeta": {
                "additionalProperties": False,
                "properties": {"meta": {"$ref": "#/components/schemas/meta"}},
            },
            "meta": {"type": "object", "additionalProperties": True},
            "datum": {
                "description": "singular item",
                "properties": {"data": {"$ref": "#/components/schemas/resource"}},
            },
            "nulltype": {"type": "object", "nullable": True, "default": None},
            "type": {
                "type": "string",
                "description": "The [type]"
                "(https://jsonapi.org/format/#document-resource-object-identification) "
                "member is used to describe resource objects that share common attributes "
                "and relationships.",
            },
            "id": {
                "type": "string",
                "description": "Each resource object’s type and id pair MUST "
                "[identify]"
                "(https://jsonapi.org/format/#document-resource-object-identification) "
                "a single, unique resource.",
            },
        },
        "parameters": {
            "include": {
                "name": "include",
                "in": "query",
                "description": "[list of included related resources]"
                "(https://jsonapi.org/format/#fetching-includes)",
                "required": False,
                "style": "form",
                "schema": {"type": "string"},
            },
            # TODO: deepObject not well defined/supported:
            #       https://github.com/OAI/OpenAPI-Specification/issues/1706
            "fields": {
                "name": "fields",
                "in": "query",
                "description": "[sparse fieldsets]"
                "(https://jsonapi.org/format/#fetching-sparse-fieldsets).\n"
                "Use fields[\\<typename\\>]=field1,field2,...,fieldN",
                "required": False,
                "style": "deepObject",
                "schema": {
                    "type": "object",
                },
                "explode": True,
            },
        },
    }

    def get_schema(self, request=None, public=False):
        """
        Generate a JSON:API OpenAPI schema.
        Overrides upstream DRF's get_schema.
        """
        # TODO: avoid copying so much of upstream get_schema()
        schema = super().get_schema(request, public)

        components_schemas = {}

        # Iterate endpoints generating per method path operations.
        paths = {}
        _, view_endpoints = self._get_paths_and_endpoints(None if public else request)

        #: `expanded_endpoints` is like view_endpoints with one extra field tacked on:
        #: - 'action' copy of current view.action (list/fetch) as this gets reset for
        # each request.
        expanded_endpoints = []
        for path, method, view in view_endpoints:
            if hasattr(view, "action") and view.action == "retrieve_related":
                expanded_endpoints += self._expand_related(
                    path, method, view, view_endpoints
                )
            else:
                expanded_endpoints.append(
                    (path, method, view, getattr(view, "action", None))
                )

        for path, method, view, action in expanded_endpoints:
            if not self.has_view_permissions(path, method, view):
                continue
            # kludge to preserve view.action as it is 'list' for the parent ViewSet
            # but the related viewset that was expanded may be either 'fetch' (to_one) or 'list'
            # (to_many). This patches the view.action appropriately so that
            # view.schema.get_operation() "does the right thing" for fetch vs. list.
            current_action = None
            if hasattr(view, "action"):
                current_action = view.action
                view.action = action
            operation = view.schema.get_operation(path, method)
            components = view.schema.get_components(path, method)
            for k in components.keys():
                if k not in components_schemas:
                    continue
                if components_schemas[k] == components[k]:
                    continue
                warnings.warn(
                    f'Schema component "{k}" has been overriden with a different value.',
                    stacklevel=1,
                )

            components_schemas.update(components)

            if hasattr(view, "action"):
                view.action = current_action
            # Normalise path for any provided mount url.
            if path.startswith("/"):
                path = path[1:]
            path = urljoin(self.url or "/", path)

            paths.setdefault(path, {})
            paths[path][method.lower()] = operation

        self.check_duplicate_operation_id(paths)

        # Compile final schema, overriding stuff from super class.
        schema["paths"] = paths
        schema["components"] = self.jsonapi_components
        schema["components"]["schemas"].update(components_schemas)

        return schema

    def _expand_related(self, path, method, view, view_endpoints):
        """
        Expand path containing .../{id}/{related_field} into list of related fields
        and **their** views, making sure toOne relationship's views are a 'fetch' and toMany
        relationship's are a 'list'.
        :param path
        :param method
        :param view
        :param view_endpoints
        :return:list[tuple(path, method, view, action)]
        """
        result = []
        serializer = view.get_serializer()
        # It's not obvious if it's allowed to have both included_ and related_ serializers,
        # so just merge both dicts.
        serializers = {}
        if hasattr(serializer, "included_serializers"):
            serializers = {**serializers, **serializer.included_serializers}
        if hasattr(serializer, "related_serializers"):
            serializers = {**serializers, **serializer.related_serializers}
        related_fields = [fs for fs in serializers.items()]

        for field, related_serializer in related_fields:
            related_view = self._find_related_view(
                view_endpoints, related_serializer, view
            )
            if related_view:
                action = self._field_is_one_or_many(field, view)
                result.append(
                    (
                        path.replace("{related_field}", field),
                        method,
                        related_view,
                        action,
                    )
                )

        return result

    def _find_related_view(self, view_endpoints, related_serializer, parent_view):
        """
        For a given related_serializer, try to find it's "parent" view instance.

        :param view_endpoints: list of all view endpoints
        :param related_serializer: the related serializer for a given related field
        :param parent_view: the parent view (used to find toMany vs. toOne).
               TODO: not actually used.
        :return:view
        """
        for _path, _method, view in view_endpoints:
            view_serializer = view.get_serializer()
            if isinstance(view_serializer, related_serializer):
                return view

        return None

    def _field_is_one_or_many(self, field, view):
        serializer = view.get_serializer()
        if isinstance(serializer.fields[field], ManyRelatedField):
            return "list"
        else:
            return "fetch"


class AutoSchema(drf_openapi.AutoSchema):
    """
    Extend DRF's openapi.AutoSchema for JSON:API serialization.
    """

    #: ignore all the media types and only generate a JSON:API schema.
    content_types = ["application/vnd.api+json"]

    def get_operation(self, path, method):
        """
        JSON:API adds some standard fields to the API response that are not in upstream DRF:
        - some that only apply to GET/HEAD methods.
        - collections
        - special handling for POST, PATCH, DELETE
        """
        operation = {}
        operation["operationId"] = self.get_operation_id(path, method)
        operation["description"] = self.get_description(path, method)

        serializer = self.get_response_serializer(path, method)

        parameters = []
        parameters += self.get_path_parameters(path, method)
        # pagination, filters only apply to GET/HEAD of collections and items
        if method in ["GET", "HEAD"]:
            parameters += self._get_include_parameters(path, method, serializer)
            parameters += self._get_fields_parameters(path, method)
            parameters += self.get_pagination_parameters(path, method)
            parameters += self.get_filter_parameters(path, method)
        operation["parameters"] = parameters
        operation["tags"] = self.get_tags(path, method)

        # get request and response code schemas
        if method == "GET":
            if is_list_view(path, method, self.view):
                self._add_get_collection_response(operation, path)
            else:
                self._add_get_item_response(operation, path)
        elif method == "POST":
            self._add_post_item_response(operation, path)
        elif method == "PATCH":
            self._add_patch_item_response(operation, path)
        elif method == "DELETE":
            # should only allow deleting a resource, not a collection
            # TODO: implement delete of a relationship in future release.
            self._add_delete_item_response(operation, path)
        return operation

    def get_operation_id(self, path, method):
        """
        The upstream DRF version creates non-unique operationIDs, because the same view is
        used for the main path as well as such as related and relationships.
        This concatenates the (mapped) method name and path as the spec allows most any
        """
        method_name = getattr(self.view, "action", method.lower())
        if is_list_view(path, method, self.view):
            action = "List"
        elif method_name not in self.method_mapping:
            action = method_name
        else:
            action = self.method_mapping[method.lower()]
        return action + path

    def _get_include_parameters(self, path, method, serializer):
        """
        includes parameter: https://jsonapi.org/format/#fetching-includes
        """
        if getattr(serializer, "included_serializers", {}):
            return [{"$ref": "#/components/parameters/include"}]
        return []

    def _get_fields_parameters(self, path, method):
        """
        sparse fieldsets https://jsonapi.org/format/#fetching-sparse-fieldsets
        """
        # TODO: See if able to identify the specific types for fields[type]=... and return this:
        # name: fields
        # in: query
        # description: '[sparse fieldsets](https://jsonapi.org/format/#fetching-sparse-fieldsets)'  # noqa: B950
        # required: true
        # style: deepObject
        # schema:
        #   type: object
        #   properties:
        #     hello:
        #       type: string  # noqa F821
        #     world:
        #       type: string  # noqa F821
        # explode: true
        return [{"$ref": "#/components/parameters/fields"}]

    def _add_get_collection_response(self, operation, path):
        """
        Add GET 200 response for a collection to operation
        """
        operation["responses"] = {
            "200": self._get_toplevel_200_response(
                operation, path, "GET", collection=True
            )
        }
        self._add_get_4xx_responses(operation)

    def _add_get_item_response(self, operation, path):
        """
        add GET 200 response for an item to operation
        """
        operation["responses"] = {
            "200": self._get_toplevel_200_response(
                operation, path, "GET", collection=False
            )
        }
        self._add_get_4xx_responses(operation)

    def _get_toplevel_200_response(self, operation, path, method, collection=True):
        """
        return top-level JSON:API GET 200 response

        :param collection: True for collections; False for individual items.

        Uses a $ref to the components.schemas.<Name> component definition.
        """
        if collection:
            data = {
                "type": "array",
                "items": get_reference(
                    self, self.get_response_serializer(path, method)
                ),
            }
        else:
            data = get_reference(self, self.get_response_serializer(path, method))

        return {
            "description": operation["operationId"],
            "content": {
                "application/vnd.api+json": {
                    "schema": {
                        "type": "object",
                        "required": ["data"],
                        "properties": {
                            "data": data,
                            "included": {
                                "type": "array",
                                "uniqueItems": True,
                                "items": {"$ref": "#/components/schemas/include"},
                            },
                            "links": {
                                "description": "Link members related to primary data",
                                "allOf": [
                                    {"$ref": "#/components/schemas/links"},
                                    {"$ref": "#/components/schemas/pagination"},
                                ],
                            },
                            "jsonapi": {"$ref": "#/components/schemas/jsonapi"},
                        },
                    }
                }
            },
        }

    def _add_post_item_response(self, operation, path):
        """
        add response for POST of an item to operation
        """
        operation["requestBody"] = self.get_request_body(path, "POST")
        operation["responses"] = {
            "201": self._get_toplevel_200_response(
                operation, path, "POST", collection=False
            )
        }
        operation["responses"]["201"]["description"] = (
            "[Created](https://jsonapi.org/format/#crud-creating-responses-201). "
            "Assigned `id` and/or any other changes are in this response."
        )
        self._add_async_response(operation)
        operation["responses"]["204"] = {
            "description": "[Created](https://jsonapi.org/format/#crud-creating-responses-204) "
            "with the supplied `id`. No other changes from what was POSTed."
        }
        self._add_post_4xx_responses(operation)

    def _add_patch_item_response(self, operation, path):
        """
        Add PATCH response for an item to operation
        """
        operation["requestBody"] = self.get_request_body(path, "PATCH")
        operation["responses"] = {
            "200": self._get_toplevel_200_response(
                operation, path, "PATCH", collection=False
            )
        }
        self._add_patch_4xx_responses(operation)

    def _add_delete_item_response(self, operation, path):
        """
        add DELETE response for item or relationship(s) to operation
        """
        # Only DELETE of relationships has a requestBody
        if isinstance(self.view, views.RelationshipView):
            operation["requestBody"] = self.get_request_body(path, "DELETE")
        self._add_delete_responses(operation)

    def get_request_body(self, path, method):
        """
        A request body is required by JSON:API for POST, PATCH, and DELETE methods.
        """
        serializer = self.get_request_serializer(path, method)
        if not isinstance(serializer, (serializers.BaseSerializer,)):
            return {}
        is_relationship = isinstance(self.view, views.RelationshipView)

        # DRF uses a $ref to the component schema definition, but this
        # doesn't work for JSON:API due to the different required fields based on
        # the method, so make those changes and inline another copy of the schema.

        # TODO: A future improvement could make this DRYer with multiple component schemas:
        # A base schema for each viewset that has no required fields
        # One subclassed from the base that requires some fields (`type` but not `id` for POST)
        # Another subclassed from base with required type/id but no required attributes (PATCH)

        if is_relationship:
            item_schema = {"$ref": "#/components/schemas/ResourceIdentifierObject"}
        else:
            item_schema = self.map_serializer(serializer)
            if method == "POST":
                # 'type' and 'id' are both required for:
                # - all relationship operations
                # - regular PATCH or DELETE
                # Only 'type' is required for POST: system may assign the 'id'.
                item_schema["required"] = ["type"]

        if "properties" in item_schema and "attributes" in item_schema["properties"]:
            # No required attributes for PATCH
            if (
                method in ["PATCH", "PUT"]
                and "required" in item_schema["properties"]["attributes"]
            ):
                del item_schema["properties"]["attributes"]["required"]
            # No read_only fields for request.
            for name, schema in (
                item_schema["properties"]["attributes"]["properties"].copy().items()
            ):  # noqa E501
                if "readOnly" in schema:
                    del item_schema["properties"]["attributes"]["properties"][name]

        if "properties" in item_schema and "relationships" in item_schema["properties"]:
            # No required relationships for PATCH
            if (
                method in ["PATCH", "PUT"]
                and "required" in item_schema["properties"]["relationships"]
            ):
                del item_schema["properties"]["relationships"]["required"]

        return {
            "content": {
                ct: {
                    "schema": {
                        "required": ["data"],
                        "properties": {"data": item_schema},
                    }
                }
                for ct in self.content_types
            }
        }

    def map_serializer(self, serializer):
        """
        Custom map_serializer that serializes the schema using the JSON:API spec.

        Non-attributes like related and identity fields, are moved to 'relationships'
        and 'links'.
        """
        # TODO: remove attributes, etc. for relationshipView??
        required = []
        attributes = {}
        relationships_required = []
        relationships = {}

        for field in serializer.fields.values():
            if isinstance(field, serializers.HyperlinkedIdentityField):
                # the 'url' is not an attribute but rather a self.link, so don't map it here.
                continue
            if isinstance(field, serializers.HiddenField):
                continue
            if isinstance(
                field,
                (
                    serializers.ManyRelatedField,
                    ManySerializerMethodResourceRelatedField,
                ),
            ):
                if field.required:
                    relationships_required.append(format_field_name(field.field_name))
                relationships[format_field_name(field.field_name)] = {
                    "$ref": "#/components/schemas/reltomany"
                }
                continue
            if isinstance(field, serializers.RelatedField):
                if field.required:
                    relationships_required.append(format_field_name(field.field_name))
                relationships[format_field_name(field.field_name)] = {
                    "$ref": "#/components/schemas/reltoone"
                }
                continue
            if field.field_name == "id":
                # ID is always provided in the root of JSON:API and removed from the
                # attributes in JSONRenderer.
                continue

            if field.required:
                required.append(format_field_name(field.field_name))

            schema = self.map_field(field)
            if field.read_only:
                schema["readOnly"] = True
            if field.write_only:
                schema["writeOnly"] = True
            if field.allow_null:
                schema["nullable"] = True
            if field.default and field.default != empty and not callable(field.default):
                schema["default"] = field.default
            if field.help_text:
                # Ensure django gettext_lazy is rendered correctly
                schema["description"] = str(field.help_text)
            self.map_field_validators(field, schema)

            attributes[format_field_name(field.field_name)] = schema

        result = {
            "type": "object",
            "required": ["type", "id"],
            "additionalProperties": False,
            "properties": {
                "type": {"$ref": "#/components/schemas/type"},
                "id": {"$ref": "#/components/schemas/id"},
                "links": {
                    "type": "object",
                    "properties": {"self": {"$ref": "#/components/schemas/link"}},
                },
            },
        }
        if attributes:
            result["properties"]["attributes"] = {
                "type": "object",
                "properties": attributes,
            }
            if required:
                result["properties"]["attributes"]["required"] = required

        if relationships:
            result["properties"]["relationships"] = {
                "type": "object",
                "properties": relationships,
            }
            if relationships_required:
                result["properties"]["relationships"][
                    "required"
                ] = relationships_required
        return result

    def _add_async_response(self, operation):
        """
        Add async response to operation
        """
        operation["responses"]["202"] = {
            "description": "Accepted for [asynchronous processing]"
            "(https://jsonapi.org/recommendations/#asynchronous-processing)",
            "content": {
                "application/vnd.api+json": {
                    "schema": {"$ref": "#/components/schemas/datum"}
                }
            },
        }

    def _failure_response(self, reason):
        """
        Return failure response reason as the description
        """
        return {
            "description": reason,
            "content": {
                "application/vnd.api+json": {
                    "schema": {"$ref": "#/components/schemas/failure"}
                }
            },
        }

    def _add_generic_failure_responses(self, operation):
        """
        Add generic failure response(s) to operation
        """
        for code, reason in [
            ("400", "bad request"),
            ("401", "not authorized"),
        ]:
            operation["responses"][code] = self._failure_response(reason)

    def _add_get_4xx_responses(self, operation):
        """
        Add generic 4xx GET responses to operation
        """
        self._add_generic_failure_responses(operation)
        for code, reason in [("404", "not found")]:
            operation["responses"][code] = self._failure_response(reason)

    def _add_post_4xx_responses(self, operation):
        """
        Add POST 4xx error responses to operation
        """
        self._add_generic_failure_responses(operation)
        for code, reason in [
            (
                "403",
                "[Forbidden](https://jsonapi.org/format/#crud-creating-responses-403)",
            ),
            (
                "404",
                "[Related resource does not exist]"
                "(https://jsonapi.org/format/#crud-creating-responses-404)",
            ),
            (
                "409",
                "[Conflict](https://jsonapi.org/format/#crud-creating-responses-409)",
            ),
        ]:
            operation["responses"][code] = self._failure_response(reason)

    def _add_patch_4xx_responses(self, operation):
        """
        Add PATCH 4xx error responses to operation
        """
        self._add_generic_failure_responses(operation)
        for code, reason in [
            (
                "403",
                "[Forbidden](https://jsonapi.org/format/#crud-updating-responses-403)",
            ),
            (
                "404",
                "[Related resource does not exist]"
                "(https://jsonapi.org/format/#crud-updating-responses-404)",
            ),
            (
                "409",
                "[Conflict]([Conflict]"
                "(https://jsonapi.org/format/#crud-updating-responses-409)",
            ),
        ]:
            operation["responses"][code] = self._failure_response(reason)

    def _add_delete_responses(self, operation):
        """
        Add generic DELETE responses to operation
        """
        # the 2xx statuses:
        operation["responses"] = {
            "200": {
                "description": "[OK](https://jsonapi.org/format/#crud-deleting-responses-200)",
                "content": {
                    "application/vnd.api+json": {
                        "schema": {"$ref": "#/components/schemas/onlymeta"}
                    }
                },
            }
        }
        self._add_async_response(operation)
        operation["responses"]["204"] = {
            "description": "[no content](https://jsonapi.org/format/#crud-deleting-responses-204)",  # noqa: B950
        }
        # the 4xx errors:
        self._add_generic_failure_responses(operation)
        for code, reason in [
            (
                "404",
                "[Resource does not exist]"
                "(https://jsonapi.org/format/#crud-deleting-responses-404)",
            ),
        ]:
            operation["responses"][code] = self._failure_response(reason)
