import warnings
from urllib.parse import urljoin

from django.db.models.fields import related_descriptors as rd
from django.utils.module_loading import import_string as import_class_from_dotted_path
from rest_framework.fields import empty
from rest_framework.relations import ManyRelatedField
from rest_framework.schemas import openapi as drf_openapi
from rest_framework.schemas.utils import is_list_view

from rest_framework_json_api import serializers
from rest_framework_json_api.views import RelationshipView


class SchemaGenerator(drf_openapi.SchemaGenerator):
    """
    Extend DRF's SchemaGenerator to implement jsonapi-flavored generateschema command.
    """
    #: These JSONAPI component definitions are referenced by the generated OAS schema.
    #: If you need to add more or change these static component definitions, extend this dict.
    jsonapi_components = {
        'schemas': {
            'jsonapi': {
                'type': 'object',
                'description': "The server's implementation",
                'properties': {
                    'version': {'type': 'string'},
                    'meta': {'$ref': '#/components/schemas/meta'}
                },
                'additionalProperties': False
            },
            'ResourceIdentifierObject': {
                'type': 'object',
                'required': ['type', 'id'],
                'additionalProperties': False,
                'properties': {
                    'type': {
                        '$ref': '#/components/schemas/type'
                    },
                    'id': {
                        '$ref': '#/components/schemas/id'
                    },
                },
            },
            'resource': {
                'type': 'object',
                'required': ['type', 'id'],
                'additionalProperties': False,
                'properties': {
                    'type': {
                        '$ref': '#/components/schemas/type'
                    },
                    'id': {
                        '$ref': '#/components/schemas/id'
                    },
                    'attributes': {
                        'type': 'object',
                        # ...
                    },
                    'relationships': {
                        'type': 'object',
                        # ...
                    },
                    'links': {
                        '$ref': '#/components/schemas/links'
                    },
                    'meta': {'$ref': '#/components/schemas/meta'},
                }
            },
            'link': {
                'oneOf': [
                    {
                        'description': "a string containing the link's URL",
                        'type': 'string',
                        'format': 'uri-reference'
                    },
                    {
                        'type': 'object',
                        'required': ['href'],
                        'properties': {
                            'href': {
                                'description': "a string containing the link's URL",
                                'type': 'string',
                                'format': 'uri-reference'
                            },
                            'meta': {'$ref': '#/components/schemas/meta'}
                        }
                    }
                ]
            },
            'links': {
                'type': 'object',
                'additionalProperties': {'$ref': '#/components/schemas/link'}
            },
            'reltoone': {
                'description': "a singular 'to-one' relationship",
                'type': 'object',
                'properties': {
                    'links': {'$ref': '#/components/schemas/relationshipLinks'},
                    'data': {'$ref': '#/components/schemas/relationshipToOne'},
                    'meta': {'$ref': '#/components/schemas/meta'}
                }
            },
            'relationshipToOne': {
                'description': "reference to other resource in a to-one relationship",
                'anyOf': [
                    {'$ref': '#/components/schemas/nulltype'},
                    {'$ref': '#/components/schemas/linkage'}
                ],
            },
            'reltomany': {
                'description': "a multiple 'to-many' relationship",
                'type': 'object',
                'properties': {
                    'links': {'$ref': '#/components/schemas/relationshipLinks'},
                    'data': {'$ref': '#/components/schemas/relationshipToMany'},
                    'meta': {'$ref': '#/components/schemas/meta'}
                }
            },
            'relationshipLinks': {
                'description': 'optional references to other resource objects',
                'type': 'object',
                'additionalProperties': True,
                'properties': {
                    'self': {'$ref': '#/components/schemas/link'},
                    'related': {'$ref': '#/components/schemas/link'}
                }
            },
            'relationshipToMany': {
                'description': "An array of objects each containing the "
                               "'type' and 'id' for to-many relationships",
                'type': 'array',
                'items': {'$ref': '#/components/schemas/linkage'},
                'uniqueItems': True
            },
            'linkage': {
                'type': 'object',
                'description': "the 'type' and 'id'",
                'required': ['type', 'id'],
                'properties': {
                    'type': {'$ref': '#/components/schemas/type'},
                    'id': {'$ref': '#/components/schemas/id'},
                    'meta': {'$ref': '#/components/schemas/meta'}
                }
            },
            'pagination': {
                'type': 'object',
                'properties': {
                    'first': {'$ref': '#/components/schemas/pageref'},
                    'last': {'$ref': '#/components/schemas/pageref'},
                    'prev': {'$ref': '#/components/schemas/pageref'},
                    'next': {'$ref': '#/components/schemas/pageref'},
                }
            },
            'pageref': {
                'oneOf': [
                    {'type': 'string', 'format': 'uri-reference'},
                    {'$ref': '#/components/schemas/nulltype'}
                ]
            },
            'failure': {
                'type': 'object',
                'required': ['errors'],
                'properties': {
                    'errors': {'$ref': '#/components/schemas/errors'},
                    'meta': {'$ref': '#/components/schemas/meta'},
                    'jsonapi': {'$ref': '#/components/schemas/jsonapi'},
                    'links': {'$ref': '#/components/schemas/links'}
                }
            },
            'errors': {
                'type': 'array',
                'items': {'$ref': '#/components/schemas/error'},
                'uniqueItems': True
            },
            'error': {
                'type': 'object',
                'additionalProperties': False,
                'properties': {
                    'id': {'type': 'string'},
                    'status': {'type': 'string'},
                    'links': {'$ref': '#/components/schemas/links'},
                    'code': {'type': 'string'},
                    'title': {'type': 'string'},
                    'detail': {'type': 'string'},
                    'source': {
                        'type': 'object',
                        'properties': {
                            'pointer': {
                                'type': 'string',
                                'description':
                                    "A [JSON Pointer](https://tools.ietf.org/html/rfc6901) "
                                    "to the associated entity in the request document "
                                    "[e.g. `/data` for a primary data object, or "
                                    "`/data/attributes/title` for a specific attribute."
                            },
                            'parameter': {
                                'type': 'string',
                                'description':
                                    "A string indicating which query parameter "
                                    "caused the error."
                            },
                            'meta': {'$ref': '#/components/schemas/meta'}
                        }
                    }
                }
            },
            'onlymeta': {
                'additionalProperties': False,
                'properties': {
                    'meta': {'$ref': '#/components/schemas/meta'}
                }
            },
            'meta': {
                'type': 'object',
                'additionalProperties': True
            },
            'datum': {
                'description': 'singular item',
                'properties': {
                    'data': {'$ref': '#/components/schemas/resource'}
                }
            },
            'nulltype': {
                'type': 'object',
                'nullable': True,
                'default': None
            },
            'type': {
                'type': 'string',
                'description':
                    'The [type]'
                    '(https://jsonapi.org/format/#document-resource-object-identification) '
                    'member is used to describe resource objects that share common attributes '
                    'and relationships.'
            },
            'id': {
                'type': 'string',
                'description':
                    "Each resource object’s type and id pair MUST "
                    "[identify]"
                    "(https://jsonapi.org/format/#document-resource-object-identification) "
                    "a single, unique resource."
            },
        },
        'parameters': {
            'include': {
                'name': 'include',
                'in': 'query',
                'description': '[list of included related resources]'
                               '(https://jsonapi.org/format/#fetching-includes)',
                'required': False,
                'style': 'form',
                'schema': {
                    'type': 'string'
                }
            },
            # TODO: deepObject not well defined/supported:
            #       https://github.com/OAI/OpenAPI-Specification/issues/1706
            'fields': {
                'name': 'fields',
                'in': 'query',
                'description': '[sparse fieldsets]'
                               '(https://jsonapi.org/format/#fetching-sparse-fieldsets).\n'
                               'Use fields[\\<typename\\>]=field1,field2,...,fieldN',
                'required': False,
                'style': 'deepObject',
                'schema': {
                    'type': 'object',
                    'properties': {
                        '<typename>': {  # placeholder for actual type names
                            'type': 'string'
                        }
                    }
                },
                'explode': True
            },
            'sort': {
                'name': 'sort',
                'in': 'query',
                'description': '[list of fields to sort by]'
                               '(https://jsonapi.org/format/#fetching-sorting)',
                'required': False,
                'style': 'form',
                'schema': {
                    'type': 'string'
                }
            },
        },
    }

    def get_schema(self, request=None, public=False):
        """
        Generate a JSONAPI OpenAPI schema.
        Overrides upstream DRF's get_schema.
        """
        # TODO: avoid copying so much of upstream get_schema()
        schema = super().get_schema(request, public)

        components_schemas = {}
        security_schemes_schemas = {}

        # Iterate endpoints generating per method path operations.
        paths = {}
        _, view_endpoints = self._get_paths_and_endpoints(None if public else request)

        #: `expanded_endpoints` is like view_endpoints with one extra field tacked on:
        #: - 'action' copy of current view.action (list/fetch) as this gets reset for each request.
        expanded_endpoints = []
        for path, method, view in view_endpoints:
            if isinstance(view, RelationshipView):
                expanded_endpoints += self._expand_relationships(path, method, view)
            elif hasattr(view, 'action') and view.action == 'retrieve_related':
                expanded_endpoints += self._expand_related(path, method, view, view_endpoints)
            else:
                expanded_endpoints.append((path, method, view,
                                           view.action if hasattr(view, 'action') else None))

        for path, method, view, action in expanded_endpoints:
            if not self.has_view_permissions(path, method, view):
                continue
            # kludge to preserve view.action as it changes "globally" for the same ViewSet
            # whether it is used for a collection, item or related serializer. _expand_related
            # sets it based on whether the related field is a toMany collection or toOne item.
            current_action = None
            if hasattr(view, 'action'):
                current_action = view.action
                view.action = action
            operation = view.schema.get_operation(path, method, action)
            components = view.schema.get_components(path, method)
            for k in components.keys():
                if k not in components_schemas:
                    continue
                if components_schemas[k] == components[k]:
                    continue
                warnings.warn(
                    'Schema component "{}" has been overriden with a different value.'.format(k))

            components_schemas.update(components)

            if hasattr(view.schema, 'get_security_schemes'):  # pragma: no cover
                security_schemes = view.schema.get_security_schemes(path, method)
            else:
                security_schemes = {}
            for k in security_schemes.keys():  # pragma: no cover
                if k not in security_schemes_schemas:
                    continue
                if security_schemes_schemas[k] == security_schemes[k]:
                    continue
                warnings.warn('Securit scheme component "{}" has been overriden with a different '
                              'value.'.format(k))
            security_schemes_schemas.update(security_schemes)  # pragma: no cover

            if hasattr(view, 'action'):
                view.action = current_action
            # Normalise path for any provided mount url.
            if path.startswith('/'):
                path = path[1:]
            path = urljoin(self.url or '/', path)

            paths.setdefault(path, {})
            paths[path][method.lower()] = operation

        self.check_duplicate_operation_id(paths)

        # Compile final schema, overriding stuff from super class.
        schema['paths'] = paths
        schema['components'] = self.jsonapi_components
        schema['components']['schemas'].update(components_schemas)
        if len(security_schemes_schemas) > 0:  # pragma: no cover
            schema['components']['securitySchemes'] = security_schemes_schemas

        return schema

    def _expand_relationships(self, path, method, view):
        """
        Expand path containing .../{id}/relationships/{related_field} into list of related fields.
        :return:list[tuple(path, method, view, action)]
        """
        queryset = view.get_queryset()
        if not queryset.model:
            return [(path, method, view, getattr(view, 'action', '')), ]
        result = []
        # TODO: what about serializer-only (non-model) fields?
        #       Shouldn't this be iterating over serializer fields rather than model fields?
        #       Look at parent view's serializer to get the list of fields.
        #       OR maybe like _expand_related?
        m = queryset.model
        for field in [f for f in dir(m) if not f.startswith('_')]:
            attr = getattr(m, field)
            if isinstance(attr, (rd.ReverseManyToOneDescriptor, rd.ForwardOneToOneDescriptor)):
                action = 'rels' if isinstance(attr, rd.ReverseManyToOneDescriptor) else 'rel'
                result.append((path.replace('{related_field}', field), method, view, action))

        return result

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
        if hasattr(serializer, 'included_serializers'):
            serializers = {**serializers, **serializer.included_serializers}
        if hasattr(serializer, 'related_serializers'):
            serializers = {**serializers, **serializer.related_serializers}
        related_fields = [fs for fs in serializers.items()]

        for field, related_serializer in related_fields:
            related_view = self._find_related_view(view_endpoints, related_serializer, view)
            if related_view:
                action = self._field_is_one_or_many(field, view)
                result.append(
                    (path.replace('{related_field}', field), method, related_view, action)
                )

        return result

    def _find_related_view(self, view_endpoints, related_serializer, parent_view):
        """
        For a given related_serializer, try to find it's "parent" view instance in view_endpoints.
        :param view_endpoints: list of all view endpoints
        :param related_serializer: the related serializer for a given related field
        :param parent_view: the parent view (used to find toMany vs. toOne).
               TODO: not actually used.
        :return:view
        """
        for path, method, view in view_endpoints:
            view_serializer = view.get_serializer()
            if not isinstance(related_serializer, type):
                related_serializer_class = import_class_from_dotted_path(related_serializer)
            else:
                related_serializer_class = related_serializer
            if isinstance(view_serializer, related_serializer_class):
                return view

        return None

    def _field_is_one_or_many(self, field, view):
        serializer = view.get_serializer()
        if isinstance(serializer.fields[field], ManyRelatedField):
            return 'list'
        else:
            return 'fetch'


class AutoSchema(drf_openapi.AutoSchema):
    """
    Extend DRF's openapi.AutoSchema for JSONAPI serialization.
    """
    #: ignore all the media types and only generate a JSONAPI schema.
    content_types = ['application/vnd.api+json']

    def get_operation(self, path, method, action=None):
        """
        JSONAPI adds some standard fields to the API response that are not in upstream DRF:
        - some that only apply to GET/HEAD methods.
        - collections
        - special handling for POST, PATCH, DELETE:

        :param action: One of the usual actions for a conventional path (list, retrieve, update,
            partial_update, destroy) or special case 'rel' or 'rels' for a singular or
            plural relationship.
        """
        operation = {}
        operation['operationId'] = self.get_operation_id(path, method)
        operation['description'] = self.get_description(path, method)
        if hasattr(self, 'get_security_requirements'):  # pragma: no cover
            security = self.get_security_requirements(path, method)
            if security is not None:
                operation['security'] = security

        parameters = []
        parameters += self.get_path_parameters(path, method)
        # pagination, filters only apply to GET/HEAD of collections and items
        if method in ['GET', 'HEAD']:
            parameters += self._get_include_parameters(path, method)
            parameters += self._get_fields_parameters(path, method)
            parameters += self._get_sort_parameters(path, method)
            parameters += self.get_pagination_parameters(path, method)
            parameters += self.get_filter_parameters(path, method)
        operation['parameters'] = parameters

        # get request and response code schemas
        if method == 'GET':
            if is_list_view(path, method, self.view):
                self._get_collection_response(operation)
            else:
                self._get_item_response(operation)
        elif method == 'POST':
            self._post_item_response(operation, path, action)
        elif method == 'PATCH':
            self._patch_item_response(operation, path, action)
        elif method == 'DELETE':
            # should only allow deleting a resource, not a collection
            # TODO: implement delete of a relationship in future release.
            self._delete_item_response(operation, path, action)
        return operation

    def get_operation_id(self, path, method):
        """
        The upstream DRF version creates non-unique operationIDs, because the same view is
        used for the main path as well as such as related and relationships.
        This concatenates the (mapped) method name and path as the spec allows most any
        """
        method_name = getattr(self.view, 'action', method.lower())
        if is_list_view(path, method, self.view):
            action = 'List'
        elif method_name not in self.method_mapping:
            action = method_name
        else:
            action = self.method_mapping[method.lower()]
        return action + path

    def _get_include_parameters(self, path, method):
        """
        includes parameter: https://jsonapi.org/format/#fetching-includes
        """
        return [{'$ref': '#/components/parameters/include'}]

    def _get_fields_parameters(self, path, method):
        """
        sparse fieldsets https://jsonapi.org/format/#fetching-sparse-fieldsets
        """
        # TODO: See if able to identify the specific types for fields[type]=... and return this:
        # name: fields
        # in: query
        # description: '[sparse fieldsets](https://jsonapi.org/format/#fetching-sparse-fieldsets)'
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
        return [{'$ref': '#/components/parameters/fields'}]

    def _get_sort_parameters(self, path, method):
        """
        sort parameter: https://jsonapi.org/format/#fetching-sorting
        """
        return [{'$ref': '#/components/parameters/sort'}]

    def _get_collection_response(self, operation):
        """
        jsonapi-structured 200 response for GET of a collection
        """
        operation['responses'] = {
            '200': self._get_toplevel_200_response(operation, collection=True)
        }
        self._add_get_4xx_responses(operation)

    def _get_item_response(self, operation):
        """
        jsonapi-structured 200 response for GET of an item
        """
        operation['responses'] = {
            '200': self._get_toplevel_200_response(operation, collection=False)
        }
        self._add_get_4xx_responses(operation)

    def _get_toplevel_200_response(self, operation, collection=True):
        """
        top-level JSONAPI GET 200 response

        :param collection: True for collections; False for individual items.

        Uses a $ref to the components.schemas.<Name> component definition.
        """
        if collection:
            data = {'type': 'array', 'items': self._get_reference(self.view.get_serializer())}
        else:
            data = self._get_reference(self.view.get_serializer())

        return {
            'description': operation['operationId'],
            'content': {
                'application/vnd.api+json': {
                    'schema': {
                        'type': 'object',
                        'required': ['data'],
                        'properties': {
                            'data': data,
                            'included': {
                                'type': 'array',
                                'uniqueItems': True,
                                'items': {
                                    '$ref': '#/components/schemas/resource'
                                }
                            },
                            'links': {
                                'description': 'Link members related to primary data',
                                'allOf': [
                                    {'$ref': '#/components/schemas/links'},
                                    {'$ref': '#/components/schemas/pagination'}
                                ]
                            },
                            'jsonapi': {
                                '$ref': '#/components/schemas/jsonapi'
                            }
                        }
                    }
                }
            }
        }

    def _post_item_response(self, operation, path, action):
        """
        jsonapi-structured response for POST of an item
        """
        operation['requestBody'] = self.get_request_body(path, 'POST', action)
        operation['responses'] = {
            '201': self._get_toplevel_200_response(operation, collection=False)
        }
        operation['responses']['201']['description'] = (
            '[Created](https://jsonapi.org/format/#crud-creating-responses-201). '
            'Assigned `id` and/or any other changes are in this response.'
        )
        self._add_async_response(operation)
        operation['responses']['204'] = {
            'description': '[Created](https://jsonapi.org/format/#crud-creating-responses-204) '
            'with the supplied `id`. No other changes from what was POSTed.'
        }
        self._add_post_4xx_responses(operation)

    def _patch_item_response(self, operation, path, action):
        """
        jsonapi-structured response for PATCH of an item
        """
        operation['requestBody'] = self.get_request_body(path, 'PATCH', action)
        operation['responses'] = {
            '200': self._get_toplevel_200_response(operation, collection=False)
        }
        self._add_patch_4xx_responses(operation)

    def _delete_item_response(self, operation, path, action):
        """
        jsonapi-structured response for DELETE of an item or relationship(s)
        """
        # Only DELETE of relationships has a requestBody
        if action in ['rels', 'rel']:
            operation['requestBody'] = self.get_request_body(path, 'DELETE', action)
        self._add_delete_responses(operation)

    def get_request_body(self, path, method, action=None):
        """
        A request body is required by jsonapi for POST, PATCH, and DELETE methods.
        This has an added parameter which is not in upstream DRF:

        :param action: None for conventional path; 'rel' or 'rels' for a singular or plural
            relationship of a related path, respectively.
        """
        serializer = self.get_serializer(path, method)
        if not isinstance(serializer, (serializers.BaseSerializer, )):
            return {}

        # DRF uses a $ref to the component definition, but this
        # doesn't work for jsonapi due to the different required fields based on
        # the method, so make those changes and inline another copy of the schema.
        # TODO: A future improvement could make this DRYer with multiple components?
        item_schema = self.map_serializer(serializer).copy()

        # 'type' and 'id' are both required for:
        # - all relationship operations
        # - regular PATCH or DELETE
        # Only 'type' is required for POST: system may assign the 'id'.
        if action in ['rels', 'rel']:
            item_schema['required'] = ['type', 'id']
        elif method in ['PATCH', 'DELETE']:
            item_schema['required'] = ['type', 'id']
        elif method == 'POST':
            item_schema['required'] = ['type']

        if 'attributes' in item_schema['properties']:
            # No required attributes for PATCH
            if method in ['PATCH', 'PUT'] and 'required' in item_schema['properties']['attributes']:
                del item_schema['properties']['attributes']['required']
            # No read_only fields for request.
            for name, schema in item_schema['properties']['attributes']['properties'].copy().items():  # noqa E501
                if 'readOnly' in schema:
                    del item_schema['properties']['attributes']['properties'][name]
        # relationships special case: plural request body (data is array of items)
        if action == 'rels':
            return {
                'content': {
                    ct: {
                        'schema': {
                            'required': ['data'],
                            'properties': {
                                'data': {
                                    'type': 'array',
                                    'items': item_schema
                                }
                            }
                        }
                    }
                    for ct in self.content_types
                }
            }
        # singular request body for all other cases
        else:
            return {
                'content': {
                    ct: {
                        'schema': {
                            'required': ['data'],
                            'properties': {
                                'data': item_schema
                            }
                        }
                    }
                    for ct in self.content_types
                }
            }

    def map_serializer(self, serializer):
        """
        Custom map_serializer that serializes the schema using the jsonapi spec.
        Non-attributes like related and identity fields, are move to 'relationships' and 'links'.
        """
        # TODO: remove attributes, etc. for relationshipView??
        required = []
        attributes = {}
        relationships = {}

        for field in serializer.fields.values():
            if isinstance(field, serializers.HyperlinkedIdentityField):
                # the 'url' is not an attribute but rather a self.link, so don't map it here.
                continue
            if isinstance(field, serializers.HiddenField):
                continue
            if isinstance(field, serializers.RelatedField):
                relationships[field.field_name] = {'$ref': '#/components/schemas/reltoone'}
                continue
            if isinstance(field, serializers.ManyRelatedField):
                relationships[field.field_name] = {'$ref': '#/components/schemas/reltomany'}
                continue

            if field.required:
                required.append(field.field_name)

            schema = self.map_field(field)
            if field.read_only:
                schema['readOnly'] = True
            if field.write_only:
                schema['writeOnly'] = True
            if field.allow_null:
                schema['nullable'] = True
            if field.default and field.default != empty:
                schema['default'] = field.default
            if field.help_text:
                # Ensure django gettext_lazy is rendered correctly
                schema['description'] = str(field.help_text)
            self.map_field_validators(field, schema)

            attributes[field.field_name] = schema

        result = {
            'type': 'object',
            'required': ['type', 'id'],
            'additionalProperties': False,
            'properties': {
                'type': {'$ref': '#/components/schemas/type'},
                'id': {'$ref': '#/components/schemas/id'},
                'links': {
                    'type': 'object',
                    'properties': {
                        'self': {'$ref': '#/components/schemas/link'}
                    }
                }
            }
        }
        if attributes:
            result['properties']['attributes'] = {
                'type': 'object',
                'properties': attributes
            }
            if required:
                result['properties']['attributes']['required'] = required

        if relationships:
            result['properties']['relationships'] = {
                'type': 'object',
                'properties': relationships
            }
        return result

    def _add_async_response(self, operation):
        operation['responses']['202'] = {
            'description': 'Accepted for [asynchronous processing]'
                           '(https://jsonapi.org/recommendations/#asynchronous-processing)',
            'content': {
                'application/vnd.api+json': {
                    'schema': {'$ref': '#/components/schemas/datum'}
                }
            }
        }

    def _failure_response(self, reason):
        return {
            'description': reason,
            'content': {
                'application/vnd.api+json': {
                    'schema': {'$ref': '#/components/schemas/failure'}
                }
            }
        }

    def _generic_failure_responses(self, operation):
        for code, reason in [('401', 'not authorized'), ]:
            operation['responses'][code] = self._failure_response(reason)

    def _add_get_4xx_responses(self, operation):
        """ Add generic responses for get """
        self._generic_failure_responses(operation)
        for code, reason in [('404', 'not found')]:
            operation['responses'][code] = self._failure_response(reason)

    def _add_post_4xx_responses(self, operation):
        """ Add error responses for post """
        self._generic_failure_responses(operation)
        for code, reason in [
            ('403', '[Forbidden](https://jsonapi.org/format/#crud-creating-responses-403)'),
            ('404', '[Related resource does not exist]'
                    '(https://jsonapi.org/format/#crud-creating-responses-404)'),
            ('409', '[Conflict](https://jsonapi.org/format/#crud-creating-responses-409)'),
        ]:
            operation['responses'][code] = self._failure_response(reason)

    def _add_patch_4xx_responses(self, operation):
        """ Add error responses for patch """
        self._generic_failure_responses(operation)
        for code, reason in [
            ('403', '[Forbidden](https://jsonapi.org/format/#crud-updating-responses-403)'),
            ('404', '[Related resource does not exist]'
                    '(https://jsonapi.org/format/#crud-updating-responses-404)'),
            ('409', '[Conflict]([Conflict]'
                    '(https://jsonapi.org/format/#crud-updating-responses-409)'),
        ]:
            operation['responses'][code] = self._failure_response(reason)

    def _add_delete_responses(self, operation):
        """ Add generic responses for delete """
        # the 2xx statuses:
        operation['responses'] = {
            '200': {
                'description': '[OK](https://jsonapi.org/format/#crud-deleting-responses-200)',
                'content': {
                    'application/vnd.api+json': {
                        'schema': {'$ref': '#/components/schemas/onlymeta'}
                    }
                }
            }
        }
        self._add_async_response(operation)
        operation['responses']['204'] = {
            'description': '[no content](https://jsonapi.org/format/#crud-deleting-responses-204)',
        }
        # the 4xx errors:
        self._generic_failure_responses(operation)
        for code, reason in [
            ('404', '[Resource does not exist]'
                    '(https://jsonapi.org/format/#crud-deleting-responses-404)'),
        ]:
            operation['responses'][code] = self._failure_response(reason)
