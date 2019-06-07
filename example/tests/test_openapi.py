# largely based on DRF's test_openapi
import pytest
from django.conf.urls import url
from django.test import RequestFactory, TestCase, override_settings
from rest_framework import VERSION as DRFVERSION
from rest_framework.request import Request

from example import views

try:
    from rest_framework_json_api.schemas.openapi import AutoSchema, SchemaGenerator
except ImportError:
    AutoSchema = SchemaGenerator = None


drf_version = tuple(int(x) for x in DRFVERSION.split('.'))
pytestmark = pytest.mark.skipif(drf_version < (3, 10), reason="requires DRF 3.10 or higher")


def create_request(path):
    factory = RequestFactory()
    request = Request(factory.get(path))
    return request


def create_view(view_cls, method, request):
    generator = SchemaGenerator()
    view = generator.create_view(view_cls.as_view(), method, request)
    return view


def create_view_with_kw(view_cls, method, request, initkwargs):
    generator = SchemaGenerator()
    view = generator.create_view(view_cls.as_view(initkwargs), method, request)
    return view


class TestOperationIntrospection(TestCase):

    def test_path_without_parameters(self):
        path = '/authors/'
        method = 'GET'

        view = create_view_with_kw(
            views.AuthorViewSet,
            method,
            create_request(path),
            {'get': 'list'}
        )
        inspector = AutoSchema()
        inspector.view = view

        operation = inspector.get_operation(path, method)
        # TODO: pick and choose portions rather than comparing the whole thing?
        assert operation == {
            'operationId': 'List/authors/',
            'security': [{'basicAuth': []}],
            'parameters': [
                {'$ref': '#/components/parameters/include'},
                {'$ref': '#/components/parameters/fields'},
                {'$ref': '#/components/parameters/sort'},
                {'name': 'page[number]', 'required': False, 'in': 'query',
                 'description': 'A page number within the paginated result set.',
                 'schema': {'type': 'integer'}},
                {'name': 'page[size]', 'required': False, 'in': 'query',
                 'description': 'Number of results to return per page.',
                 'schema': {'type': 'integer'}},
                {'name': 'sort', 'required': False, 'in': 'query',
                 'description': 'Which field to use when ordering the results.',
                 'schema': {'type': 'string'}},
                {'name': 'filter[search]', 'required': False, 'in': 'query',
                 'description': 'A search term.', 'schema': {'type': 'string'}}
            ],
            'responses': {
                '200': {
                    'description': 'List/authors/',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {
                                'type': 'object',
                                'required': ['data'],
                                'properties': {
                                    'data': {
                                        'type': 'array',
                                        'items': {
                                            'type': 'object',
                                            'required': ['type', 'id'],
                                            'additionalProperties': False,
                                            'properties': {
                                                'type': {'$ref': '#/components/schemas/type'},
                                                'id': {'$ref': '#/components/schemas/id'},
                                                'links': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'self': {
                                                            '$ref': '#/components/schemas/link'
                                                        }
                                                    }
                                                },
                                                'attributes': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'name': {
                                                            'type': 'string',
                                                            'maxLength': 50
                                                        },
                                                        'email': {
                                                            'type': 'string',
                                                            'format': 'email',
                                                            'maxLength': 254
                                                        }
                                                    },
                                                    'required': ['name', 'email']
                                                },
                                                'relationships': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'bio': {
                                                            '$ref':
                                                                '#/components/schemas/reltoone'
                                                        },
                                                        'entries': {
                                                            '$ref':
                                                                '#/components/schemas/reltomany'
                                                        },
                                                        'comments': {
                                                            '$ref':
                                                                '#/components/schemas/reltomany'
                                                        },
                                                        'first_entry': {
                                                            '$ref':
                                                                '#/components/schemas/reltoone'
                                                        },
                                                        'type': {
                                                            '$ref': '#/components/schemas/reltoone'
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'included': {
                                        'type': 'array',
                                        'uniqueItems': True,
                                        'items': {'$ref': '#/components/schemas/resource'}
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
                },
                '401': {
                    'description': 'not authorized',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/failure'}
                        }
                    }
                },
                '404': {
                    'description': 'not found',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/failure'}
                        }
                    }
                }
            }
        }

    def test_path_with_id_parameter(self):
        path = '/authors/{id}/'
        method = 'GET'

        view = create_view_with_kw(
            views.AuthorViewSet,
            method,
            create_request(path),
            {'get': 'retrieve'}
        )
        inspector = AutoSchema()
        inspector.view = view

        operation = inspector.get_operation(path, method)
        assert operation == {
            'operationId': 'retrieve/authors/{id}/',
            'security': [{'basicAuth': []}],
            'parameters': [
                {
                    'name': 'id',
                    'in': 'path',
                    'required': True,
                    'description': 'A unique integer value identifying this author.',
                    'schema': {'type': 'string'}
                },
                {'$ref': '#/components/parameters/include'},
                {'$ref': '#/components/parameters/fields'},
                {'$ref': '#/components/parameters/sort'},
                {
                    'name': 'sort', 'required': False, 'in': 'query',
                    'description': 'Which field to use when ordering the results.',
                    'schema': {'type': 'string'}
                },
                {
                    'name': 'filter[search]', 'required': False, 'in': 'query',
                    'description': 'A search term.',
                    'schema': {'type': 'string'}
                }
            ],
            'responses': {
                '200': {
                    'description': 'retrieve/authors/{id}/',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {
                                'type': 'object',
                                'required': ['data'],
                                'properties': {
                                    'data': {
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
                                            },
                                            'attributes': {
                                                'type': 'object',
                                                'properties': {
                                                    'name': {
                                                        'type': 'string',
                                                        'maxLength': 50
                                                    },
                                                    'email': {
                                                        'type': 'string',
                                                        'format': 'email',
                                                        'maxLength': 254
                                                    }
                                                },
                                                'required': ['name', 'email']
                                            },
                                            'relationships': {
                                                'type': 'object',
                                                'properties': {
                                                    'bio': {
                                                        '$ref': '#/components/schemas/reltoone'
                                                    },
                                                    'entries': {
                                                        '$ref': '#/components/schemas/reltomany'
                                                    },
                                                    'comments': {
                                                        '$ref': '#/components/schemas/reltomany'
                                                    },
                                                    'first_entry': {
                                                        '$ref': '#/components/schemas/reltoone'
                                                    },
                                                    'type': {
                                                        '$ref': '#/components/schemas/reltoone'
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'included': {
                                        'type': 'array',
                                        'uniqueItems': True,
                                        'items': {'$ref': '#/components/schemas/resource'}
                                    },
                                    'links': {
                                        'description': 'Link members related to primary data',
                                        'allOf': [
                                            {'$ref': '#/components/schemas/links'},
                                            {'$ref': '#/components/schemas/pagination'}
                                        ]
                                    },
                                    'jsonapi': {'$ref': '#/components/schemas/jsonapi'}
                                }
                            }
                        }
                    }
                },
                '401': {
                    'description': 'not authorized',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/failure'}
                        }
                    }
                },
                '404': {
                    'description': 'not found',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/failure'}
                        }
                    }
                }
            }
        }

    def test_post_request(self):
        method = 'POST'
        path = '/authors/'

        view = create_view_with_kw(
            views.AuthorViewSet,
            method,
            create_request(path),
            {'post': 'create'}
        )
        inspector = AutoSchema()
        inspector.view = view

        operation = inspector.get_operation(path, method)
        assert operation == {
            'operationId': 'create/authors/',
            'security': [{'basicAuth': []}],
            'parameters': [],
            'requestBody': {
                'content': {
                    'application/vnd.api+json': {
                        'schema': {
                            'required': ['data'],
                            'properties': {
                                'data': {
                                    'type': 'object',
                                    'required': ['type'],
                                    'additionalProperties': False,
                                    'properties': {
                                        'type': {'$ref': '#/components/schemas/type'},
                                        'id': {'$ref': '#/components/schemas/id'},
                                        'links': {
                                            'type': 'object',
                                            'properties': {
                                                'self': {'$ref': '#/components/schemas/link'}
                                            }
                                        },
                                        'attributes': {
                                            'type': 'object',
                                            'properties': {
                                                'name': {
                                                    'type': 'string',
                                                    'maxLength': 50
                                                },
                                                'email': {
                                                    'type': 'string',
                                                    'format': 'email',
                                                    'maxLength': 254}
                                            },
                                            'required': ['name', 'email']
                                        },
                                        'relationships': {
                                            'type': 'object',
                                            'properties': {
                                                'bio': {
                                                    '$ref': '#/components/schemas/reltoone'
                                                },
                                                'entries': {
                                                    '$ref': '#/components/schemas/reltomany'
                                                },
                                                'comments': {
                                                    '$ref': '#/components/schemas/reltomany'
                                                },
                                                'first_entry': {
                                                    '$ref': '#/components/schemas/reltoone'
                                                }, 'type': {
                                                    '$ref': '#/components/schemas/reltoone'
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            'responses': {
                '201': {
                    'description':
                        '[Created](https://jsonapi.org/format/#crud-creating-responses-201). '
                        'Assigned `id` and/or any other changes are in this response.',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {
                                'type': 'object',
                                'required': ['data'],
                                'properties': {
                                    'data': {
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
                                            },
                                            'attributes': {
                                                'type': 'object',
                                                'properties': {
                                                    'name': {
                                                        'type': 'string',
                                                        'maxLength': 50
                                                    },
                                                    'email': {
                                                        'type': 'string',
                                                        'format': 'email',
                                                        'maxLength': 254
                                                    }
                                                },
                                                'required': ['name', 'email']
                                            },
                                            'relationships': {
                                                'type': 'object',
                                                'properties': {
                                                    'bio': {
                                                        '$ref': '#/components/schemas/reltoone'
                                                    },
                                                    'entries': {
                                                        '$ref': '#/components/schemas/reltomany'
                                                    },
                                                    'comments': {
                                                        '$ref': '#/components/schemas/reltomany'
                                                    },
                                                    'first_entry': {
                                                        '$ref': '#/components/schemas/reltoone'
                                                    },
                                                    'type': {
                                                        '$ref': '#/components/schemas/reltoone'
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'included': {
                                        'type': 'array',
                                        'uniqueItems': True,
                                        'items': {'$ref': '#/components/schemas/resource'}
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
                },
                '202': {
                    'description': 'Accepted for [asynchronous processing]'
                                   '(https://jsonapi.org/recommendations/#asynchronous-processing)',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/datum'}
                        }
                    }
                },
                '204': {
                    'description': '[Created](https://jsonapi.org/format/'
                                   '#crud-creating-responses-204) with the supplied `id`. '
                                   'No other changes from what was POSTed.'
                },
                '401': {
                    'description': 'not authorized',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/failure'}
                        }
                    }
                },
                '403': {
                    'description':
                        '[Forbidden](https://jsonapi.org/format/#crud-creating-responses-403)',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/failure'}
                        }
                    }
                },
                '404': {
                    'description': '[Related resource does not exist]'
                                   '(https://jsonapi.org/format/#crud-creating-responses-404)',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/failure'}
                        }
                    }
                },
                '409': {
                    'description':
                        '[Conflict](https://jsonapi.org/format/#crud-creating-responses-409)',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/failure'}
                        }
                    }
                }
            }
        }

    def test_patch_request(self):
        method = 'PATCH'
        path = '/authors/{id}'

        view = create_view_with_kw(
            views.AuthorViewSet,
            method,
            create_request(path),
            {'patch': 'update'}
        )
        inspector = AutoSchema()
        inspector.view = view

        operation = inspector.get_operation(path, method)
        assert operation == {
            'operationId': 'update/authors/{id}',
            'security': [{'basicAuth': []}],
            'parameters': [
                {
                    'name': 'id',
                    'in': 'path',
                    'required': True,
                    'description': 'A unique integer value identifying this author.',
                    'schema': {'type': 'string'}
                }
            ],
            'requestBody': {
                'content': {
                    'application/vnd.api+json': {
                        'schema': {
                            'required': ['data'],
                            'properties': {
                                'data': {
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
                                        },
                                        'attributes': {
                                            'type': 'object',
                                            'properties': {
                                                'name': {
                                                    'type': 'string',
                                                    'maxLength': 50
                                                },
                                                'email': {
                                                    'type': 'string',
                                                    'format': 'email',
                                                    'maxLength': 254
                                                }
                                            }
                                        },
                                        'relationships': {
                                            'type': 'object',
                                            'properties': {
                                                'bio': {
                                                    '$ref': '#/components/schemas/reltoone'
                                                },
                                                'entries': {
                                                    '$ref': '#/components/schemas/reltomany'
                                                },
                                                'comments': {
                                                    '$ref': '#/components/schemas/reltomany'
                                                },
                                                'first_entry': {
                                                    '$ref': '#/components/schemas/reltoone'
                                                },
                                                'type': {
                                                    '$ref': '#/components/schemas/reltoone'
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            'responses': {
                '200': {
                    'description': 'update/authors/{id}',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {
                                'type': 'object',
                                'required': ['data'],
                                'properties': {
                                    'data': {
                                        'type': 'object',
                                        'required': ['type', 'id'],
                                        'additionalProperties': False,
                                        'properties': {
                                            'type': {'$ref': '#/components/schemas/type'},
                                            'id': {'$ref': '#/components/schemas/id'},
                                            'links': {
                                                'type': 'object',
                                                'properties': {
                                                    'self': {
                                                        '$ref': '#/components/schemas/link'
                                                    }
                                                }
                                            },
                                            'attributes': {
                                                'type': 'object',
                                                'properties': {
                                                    'name': {
                                                        'type': 'string',
                                                        'maxLength': 50
                                                    },
                                                    'email': {
                                                        'type': 'string',
                                                        'format': 'email',
                                                        'maxLength': 254
                                                    }
                                                },
                                                'required': ['name', 'email']
                                            },
                                            'relationships': {
                                                'type': 'object',
                                                'properties': {
                                                    'bio': {
                                                        '$ref': '#/components/schemas/reltoone'
                                                    },
                                                    'entries': {
                                                        '$ref': '#/components/schemas/reltomany'
                                                    },
                                                    'comments': {
                                                        '$ref': '#/components/schemas/reltomany'
                                                    },
                                                    'first_entry': {
                                                        '$ref': '#/components/schemas/reltoone'
                                                    },
                                                    'type': {
                                                        '$ref': '#/components/schemas/reltoone'
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    'included': {
                                        'type': 'array',
                                        'uniqueItems': True,
                                        'items': {
                                            '$ref': '#/components/schemas/resource'
                                        }
                                    },
                                    'links': {
                                        'description':
                                            'Link members related to primary data',
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
                },
                '401': {
                    'description': 'not authorized',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/failure'}
                        }
                    }
                },
                '403': {
                    'description':
                        '[Forbidden](https://jsonapi.org/format/#crud-updating-responses-403)',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/failure'}
                        }
                    }
                },
                '404': {
                    'description':
                        '[Related resource does not exist]'
                        '(https://jsonapi.org/format/#crud-updating-responses-404)',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/failure'}
                        }
                    }
                },
                '409': {
                    'description':
                        '[Conflict]([Conflict]'
                        '(https://jsonapi.org/format/#crud-updating-responses-409)',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/failure'}
                        }
                    }
                }
            }
        }

    def test_delete_request(self):
        method = 'DELETE'
        path = '/authors/{id}'

        view = create_view_with_kw(
            views.AuthorViewSet,
            method,
            create_request(path),
            {'delete': 'delete'}
        )
        inspector = AutoSchema()
        inspector.view = view

        operation = inspector.get_operation(path, method)
        assert operation == {
            'operationId': 'Destroy/authors/{id}',
            'security': [{'basicAuth': []}],
            'parameters': [
                {
                    'name': 'id',
                    'in': 'path',
                    'required': True,
                    'description': 'A unique integer value identifying this author.',
                    'schema': {'type': 'string'}
                }
            ],
            'responses': {
                '200': {
                    'description':
                        '[OK](https://jsonapi.org/format/#crud-deleting-responses-200)',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/onlymeta'}
                        }
                    }
                },
                '202': {
                    'description':
                        'Accepted for [asynchronous processing]'
                        '(https://jsonapi.org/recommendations/#asynchronous-processing)',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/datum'}
                        }
                    }
                },
                '204': {
                    'description':
                        '[no content](https://jsonapi.org/format/#crud-deleting-responses-204)'
                },
                '401': {
                    'description': 'not authorized',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/failure'}
                        }
                    }
                },
                '404': {
                    'description':
                        '[Resource does not exist]'
                        '(https://jsonapi.org/format/#crud-deleting-responses-404)',
                    'content': {
                        'application/vnd.api+json': {
                            'schema': {'$ref': '#/components/schemas/failure'}
                        }
                    }
                }
            }
        }

    # TODO: figure these out
    # def test_retrieve_relationships(self):
    #     path = '/authors/{id}/relationships/bio/'
    #     method = 'GET'
    #
    #     view = create_view_with_kw(
    #         views.AuthorRelationshipView,
    #         method,
    #         create_request(path),
    #         {'get': 'retrieve'}
    #     )
    #     inspector = AutoSchema()
    #     inspector.view = view
    #
    #     operation = inspector.get_operation(path, method)
    #     assert operation == {}

    # def test_retrieve_related(self):
    #     path = '/authors/{id}/{related_field}/'
    #     method = 'GET'
    #
    #     view = create_view_with_kw(
    #         views.AuthorViewSet,
    #         method,
    #         create_request(path),
    #         {'get': 'retrieve_related',
    #          'related_field': 'bio'}
    #     )
    #     inspector = AutoSchema()
    #     inspector.view = view
    #
    #     operation = inspector.get_operation(path, method)
    #     assert operation == {}

@override_settings(
    REST_FRAMEWORK={'DEFAULT_SCHEMA_CLASS': 'rest_framework_json_api.schemas.openapi.AutoSchema'})
class TestGenerator(TestCase):
    def test_schema_construction(self):
        """Construction of the top level dictionary."""
        patterns = [
            url(r'^authors/?$', views.AuthorViewSet.as_view({'get': 'list'})),
        ]
        generator = SchemaGenerator(patterns=patterns)

        request = create_request('/')
        schema = generator.get_schema(request=request)

        assert 'openapi' in schema
        assert 'info' in schema
        assert 'paths' in schema
        assert 'components' in schema
