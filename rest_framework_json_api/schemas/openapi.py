import warnings
from urllib.parse import urljoin

from django.conf import settings
from django.db.models.fields import related_descriptors as rd
from django.utils.module_loading import import_string as import_class_from_dotted_path
try:
    from oauth2_provider.contrib.rest_framework.authentication import OAuth2Authentication
    from oauth2_provider.contrib.rest_framework.permissions import TokenMatchesOASRequirements
except ImportError:
    OAuth2Authentication = None
    TokenMatchesOASRequirements = None
from rest_framework import exceptions
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.relations import ManyRelatedField
from rest_framework.schemas import openapi as drf_openapi
from rest_framework.schemas.utils import is_list_view

from rest_framework_json_api import serializers
from rest_framework_json_api.views import RelationshipView

#: static OAS 3.0 component definitions that are referenced by AutoSchema.
JSONAPI_COMPONENTS = {
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
                           '(https://jsonapi.org/format/#fetching-sparse-fieldsets)',
            'required': False,
            'style': 'deepObject',
            'schema': {
                'type': 'object',
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


class SchemaGenerator(drf_openapi.SchemaGenerator):
    """
    Extend DRF's SchemaGenerator to implement jsonapi-flavored generateschema command
    """
    def __init__(self, *args, **kwargs):
        self.openapi_schema = {}
        return super().__init__(*args, **kwargs)

    def get_schema(self, request=None, public=False):
        """
        Generate a JSONAPI OpenAPI schema.
        """
        self._initialise_endpoints()

        paths = self.get_paths(None if public else request)
        if not paths:
            return None
        schema = {
            'openapi': '3.0.2',
            'info': self.get_info(),
            'paths': paths,
            'components': JSONAPI_COMPONENTS,
        }

        return {**schema, **self.openapi_schema}

    def get_paths(self, request=None):
        """
        **Replacement** for rest_framework.schemas.openapi.SchemaGenerator.get_paths():
        - expand the paths for RelationshipViews and retrieve_related actions:
          {related_field} gets replaced by the related field names.
        - Merges in any openapi_schema initializer that the view has.
        """
        result = {}

        paths, view_endpoints = self._get_paths_and_endpoints(request)

        # Only generate the path prefix for paths that will be included
        if not paths:
            return None

        #: `expanded_endpoints` is like view_endpoints with one extra field tacked on:
        #: - 'action' copy of current view.action (list/fetch) as this gets reset for each request.
        # TODO: define an endpoint_inspector_cls that extends EndpointEnumerator
        #       instead of doing it here.
        expanded_endpoints = []
        for path, method, view in view_endpoints:
            if isinstance(view, RelationshipView):
                expanded_endpoints += self._expand_relationships(path, method, view)
            elif view.action == 'retrieve_related':
                expanded_endpoints += self._expand_related(path, method, view, view_endpoints)
            else:
                expanded_endpoints.append((path, method, view, view.action))

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
            if hasattr(view, 'action'):
                view.action = current_action
            operation['description'] = operation['operationId']  # TODO: kludge
            if 'responses' in operation and '200' in operation['responses']:
                operation['responses']['200']['description'] = operation['operationId']  # TODO:!
            # Normalise path for any provided mount url.
            if path.startswith('/'):
                path = path[1:]
            path = urljoin(self.url or '/', path)

            result.setdefault(path, {})
            result[path][method.lower()] = operation
            if hasattr(view.schema, 'openapi_schema'):
                # TODO: shallow or deep merge?
                self.openapi_schema = {**self.openapi_schema, **view.schema.openapi_schema}

        return result

    def _expand_relationships(self, path, method, view):
        """
        Expand path containing .../{id}/relationships/{related_field} into list of related fields.
        :return:list[tuple(path, method, view, action)]
        """
        queryset = view.get_queryset()
        if not queryset or not queryset.model:
            return [(path, method, view, getattr(view, 'action', '')), ]
        result = []
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
        if hasattr(serializer, 'related_serializers'):
            related_fields = [fs for fs in serializer.related_serializers.items()]
        elif hasattr(serializer, 'included_serializers'):
            related_fields = [fs for fs in serializer.included_serializers.items()]
        else:
            related_fields = []
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
    content_types = ['application/vnd.api+json']

    def __init__(self, openapi_schema={}):
        """
        Initialize the JSONAPI OAS schema generator
        :param openapi_schema: dict: OAS 3.0 document with initial values.
        """
        super().__init__()
        #: allow initialization of OAS schema doc
        self.openapi_schema = openapi_schema
        # static JSONAPI fields that get $ref'd to in the view mappings
        jsonapi_ref = {
            'components': JSONAPI_COMPONENTS
        }
        # merge in our reference data on top of anything provided by the init.
        # TODO: shallow or deep merge?
        self.openapi_schema = {**self.openapi_schema, **jsonapi_ref}

    def get_operation(self, path, method, action=None):
        """ basically a copy of AutoSchema.get_operation """
        operation = {}
        operation['operationId'] = self._get_operation_id(path, method)
        operation['security'] = self._get_security(path, method)

        parameters = []
        parameters += self._get_path_parameters(path, method)
        # pagination, filters only apply to GET/HEAD of collections and items
        if method in ['GET', 'HEAD']:
            parameters += self._get_include_parameters(path, method)
            parameters += self._get_fields_parameters(path, method)
            parameters += self._get_sort_parameters(path, method)
            parameters += self._get_pagination_parameters(path, method)
            parameters += self._get_filter_parameters(path, method)
        operation['parameters'] = parameters

        # get request and response code schemas
        if method == 'GET':
            if is_list_view(path, method, self.view):
                self._get_collection(operation)
            else:
                self._get_item(operation)
        elif method == 'POST':
            self._post_item(operation, path, action)
        elif method == 'PATCH':
            self._patch_item(operation, path, action)
        elif method == 'DELETE':
            # should only allow deleting a resource, not a collection
            # TODO: delete of a relationship is different.
            self._delete_item(operation, path, action)
        return operation

    def _get_operation_id(self, path, method):
        """ create a unique operationId """
        # The DRF version creates non-unique operationIDs, especially when the same view is used
        # for different paths. Just make a simple concatenation of (mapped) method name and path.
        method_name = getattr(self.view, 'action', method.lower())
        if is_list_view(path, method, self.view):
            action = 'List'
        elif method_name not in self.method_mapping:
            action = method_name
        else:
            action = self.method_mapping[method.lower()]
        return action + path

    def _get_security(self, path, method):
        # TODO: flesh this out and move to DRF openapi.
        content = []
        for auth_class in self.view.authentication_classes:
            if issubclass(auth_class, BasicAuthentication):
                content.append({'basicAuth': []})
                self.openapi_schema['components']['securitySchemes'] = {
                    'basicAuth': {'type': 'http', 'scheme': 'basic'}
                }
                continue
            if issubclass(auth_class, SessionAuthentication):
                continue                # TODO: can this be represented?
            # TODO: how to do this? needs permission_classes, etc. and is not super-consistent.
            if OAuth2Authentication and issubclass(auth_class, OAuth2Authentication):
                content += self._get_oauth_security(path, method)
                continue
        return content

    def _get_oauth_security(self, path, method):
        """
        Creates `#components/securitySchemes/oauth` and returns `.../security/oauth`
        when using Django OAuth Toolkit.
        """
        # TODO: make DOT an optional import
        # openIdConnect type not currently supported by Swagger-UI
        # 'openIdConnectUrl': settings.OAUTH2_SERVER + '/.well-known/openid-configuration'
        if not hasattr(settings, 'OAUTH2_CONFIG'):
            return []
        self.openapi_schema['components']['securitySchemes']['oauth'] = {
            'type': 'oauth2',
            'description': 'oauth2.0 service',
        }
        flows = {}
        if 'authorization_code' in settings.OAUTH2_CONFIG['grant_types_supported']:
            flows['authorizationCode'] = {
                'authorizationUrl': settings.OAUTH2_CONFIG['authorization_endpoint'],
                'tokenUrl': settings.OAUTH2_CONFIG['token_endpoint'],
                'refreshUrl': settings.OAUTH2_CONFIG['token_endpoint'],
                'scopes': {s: s for s in settings.OAUTH2_CONFIG['scopes_supported']}
            }
        if 'implicit' in settings.OAUTH2_CONFIG['grant_types_supported']:
            flows['implicit'] = {
                'authorizationUrl': settings.OAUTH2_CONFIG['authorization_endpoint'],
                'scopes': {s: s for s in settings.OAUTH2_CONFIG['scopes_supported']}
            }
        if 'client_credentials' in settings.OAUTH2_CONFIG['grant_types_supported']:
            flows['clientCredentials'] = {
                'tokenUrl': settings.OAUTH2_CONFIG['token_endpoint'],
                'refreshUrl': settings.OAUTH2_CONFIG['token_endpoint'],
                'scopes': {s: s for s in settings.OAUTH2_CONFIG['scopes_supported']}
            }
        if 'password' in settings.OAUTH2_CONFIG['grant_types_supported']:
            flows['password'] = {
                'tokenUrl': settings.OAUTH2_CONFIG['token_endpoint'],
                'refreshUrl': settings.OAUTH2_CONFIG['token_endpoint'],
                'scopes': {s: s for s in settings.OAUTH2_CONFIG['scopes_supported']}
            }
        self.openapi_schema['components']['securitySchemes']['oauth']['flows'] = flows
        # TODO: add JWT and SAML2 bearer
        content = []
        for perm_class in self.view.permission_classes:
            if TokenMatchesOASRequirements and issubclass(perm_class.perms_or_conds[0], TokenMatchesOASRequirements):
                alt_scopes = self.view.required_alternate_scopes
                if method not in alt_scopes:
                    continue
                for scopes in alt_scopes[method]:
                    content.append({'oauth': scopes})
        return content

    def _get_include_parameters(self, path, method):
        """
        includes parameter: https://jsonapi.org/format/#fetching-includes
        """
        return [{'$ref': '#/components/parameters/include'}]

    def _get_fields_parameters(self, path, method):
        """
        sparse fieldsets https://jsonapi.org/format/#fetching-sparse-fieldsets
        """
        return [{'$ref': '#/components/parameters/fields'}]

    def _get_sort_parameters(self, path, method):
        """
        sort parameter: https://jsonapi.org/format/#fetching-sorting
        """
        return [{'$ref': '#/components/parameters/sort'}]

    def _get_collection(self, operation):
        """
        jsonapi-structured 200 response for GET of a collection
        """
        operation['responses'] = {
            '200': self._get_toplevel_200_response(operation, collection=True)
        }
        self._add_get_4xx_responses(operation)

    def _get_item(self, operation):
        """ jsonapi-structured response for GET of an item """
        operation['responses'] = {
            '200': self._get_toplevel_200_response(operation, collection=False)
        }
        self._add_get_4xx_responses(operation)

    def _get_toplevel_200_response(self, operation, collection=True):
        """ top-level JSONAPI GET 200 response """
        if collection:
            data = {'type': 'array', 'items': self._get_item_schema(operation)}
        else:
            data = self._get_item_schema(operation)

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

    def _get_item_schema(self, operation):
        """
        get the schema for item
        """
        content = {}
        view = self.view
        if hasattr(view, 'get_serializer'):
            try:
                serializer = view.get_serializer()
            except exceptions.APIException:
                serializer = None
                warnings.warn('{}.get_serializer() raised an exception during '
                              'schema generation. Serializer fields will not be '
                              'generated.'.format(view.__class__.__name__))

            if isinstance(serializer, serializers.BaseSerializer):
                content = self._map_serializer(serializer)
                # No write_only fields for response.
                for name, schema in content['properties'].copy().items():
                    if 'writeOnly' in schema:
                        del content['properties'][name]
                        content['required'] = [f for f in content['required'] if f != name]
                content['properties']['type'] = {'$ref': '#/components/schemas/type'}
                content['properties']['id'] = {'$ref': '#/components/schemas/id'}

        return content

    def _post_item(self, operation, path, action):
        """ jsonapi-strucutred response for POST of an item """
        operation['requestBody'] = self._get_request_body(path, 'POST', action)
        operation['responses'] = {
            '201': self._get_toplevel_200_response(operation, collection=False)
        }
        operation['responses']['201']['description'] = \
            '[Created](https://jsonapi.org/format/#crud-creating-responses-201). '\
            'Assigned `id` and/or any other changes are in this response.'
        self._add_async_response(operation)
        operation['responses']['204'] = {
            'description': '[Created](https://jsonapi.org/format/#crud-creating-responses-204) '
            'with the supplied `id`. No other changes from what was POSTed.'
        }
        self._add_post_4xx_responses(operation)

    def _patch_item(self, operation, path, action):
        """ jsomapi-strucutred response for PATCH of an item """
        operation['requestBody'] = self._get_request_body(path, 'PATCH', action)
        operation['responses'] = {
            '200': self._get_toplevel_200_response(operation, collection=False)
        }
        self._add_patch_4xx_responses(operation)

    def _delete_item(self, operation, path, action):
        """ jsonapi-structured response for DELETE of an item or relationship? """
        # Only DELETE of relationships has a requestBody
        if action in ['rels', 'rel']:
            operation['requestBody'] = self._get_request_body(path, 'DELETE', action)

        self._add_delete_responses(operation)

    def _get_request_body(self, path, method, action):
        """ jsonapi-flavored request_body """
        # TODO: if a RelationshipView, check for toMany (data array) vs. toOne.
        content = {}
        view = self.view

        if not hasattr(view, 'get_serializer'):
            return {}

        try:
            serializer = view.get_serializer()
        except exceptions.APIException:
            serializer = None
            warnings.warn('{}.get_serializer() raised an exception during '
                          'schema generation. Serializer fields will not be '
                          'generated for {} {}.'
                          .format(view.__class__.__name__, method, path))

        # ResourceIdentifierObjectSerializer
        if not isinstance(serializer, (serializers.BaseSerializer, )):
            return {}

        content = self._map_serializer(serializer)

        # 'type' and 'id' are both required for:
        # - all relationship operations
        # - regular PATCH or DELETE
        # Only 'type' is required for POST: system may assign the 'id'.
        if action in ['rels', 'rel']:
            content['required'] = ['type', 'id']
        elif method in ['PATCH', 'DELETE']:
            content['required'] = ['type', 'id']
        elif method == 'POST':
            content['required'] = ['type']

        if 'attributes' in content['properties']:
            # No required attributes for PATCH
            if method in ['PATCH', 'PUT'] and 'required' in content['properties']['attributes']:
                del content['properties']['attributes']['required']
            # No read_only fields for request.
            for name, schema in content['properties']['attributes']['properties'].copy().items():
                if 'readOnly' in schema:
                    del content['properties']['attributes']['properties'][name]
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
                                    'items': content
                                }
                            }
                        }
                    }
                    for ct in self.content_types
                }
            }
        else:
            return {
                'content': {
                    ct: {
                        'schema': {
                            'required': ['data'],
                            'properties': {
                                'data': content
                            }
                        }
                    }
                    for ct in self.content_types
                }
            }

    def _map_serializer(self, serializer):
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

            schema = self._map_field(field)
            if field.help_text:
                schema['description'] = field.help_text
            self._map_field_validators(field.validators, schema)
            if field.read_only:
                schema['readOnly'] = True
            if field.write_only:
                schema['writeOnly'] = True
            if field.allow_null:
                schema['nullable'] = True

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
        if relationships:
            result['properties']['relationships'] = {
                'type': 'object',
                'properties': relationships
            }
        if required:
            result['properties']['attributes']['required'] = required
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
