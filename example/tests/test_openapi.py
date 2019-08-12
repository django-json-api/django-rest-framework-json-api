# largely based on DRF's test_openapi
import json

from django.conf.urls import url
from django.test import RequestFactory, override_settings
from rest_framework.request import Request

from rest_framework_json_api.schemas.openapi import AutoSchema, SchemaGenerator
from rest_framework_json_api.views import ModelViewSet

from example import models, serializers, views


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


def test_path_without_parameters(snapshot):
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
    snapshot.assert_match(json.dumps(operation, indent=2, sort_keys=True))


def test_path_with_id_parameter(snapshot):
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
    snapshot.assert_match(json.dumps(operation, indent=2, sort_keys=True))


def test_post_request(snapshot):
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
    snapshot.assert_match(json.dumps(operation, indent=2, sort_keys=True))


def test_patch_request(snapshot):
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
    snapshot.assert_match(json.dumps(operation, indent=2, sort_keys=True))


def test_delete_request(snapshot):
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
    snapshot.assert_match(json.dumps(operation, indent=2, sort_keys=True))


@override_settings(REST_FRAMEWORK={
    'DEFAULT_SCHEMA_CLASS': 'rest_framework_json_api.schemas.openapi.AutoSchema'})
def test_schema_construction():
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


# TODO: figure these out
def test_schema_related():
    class AuthorBioViewSet(ModelViewSet):
        queryset = models.AuthorBio.objects.all()
        serializer_class = serializers.AuthorBioSerializer

    patterns = [
        url(r'^authors/(?P<pk>[^/.]+)/(?P<related_field>\w+)/$',
            views.AuthorViewSet.as_view({'get': 'retrieve_related'}),
            name='author-related'),
        url(r'^bios/(?P<pk>[^/.]+)/$',
            AuthorBioViewSet,
            name='author-bio')
    ]
    generator = SchemaGenerator(patterns=patterns)

    request = create_request('/authors/123/bio/')
    schema = generator.get_schema(request=request)
    # TODO: finish this test
    print(schema)

# def test_retrieve_relationships():
#     path = '/authors/{id}/relationships/bio/'
#     method = 'GET'
#
#     view = create_view_with_kw(
#         views.AuthorViewSet,
#         method,
#         create_request(path),
#         {'get': 'retrieve_related'}
#     )
#     inspector = AutoSchema()
#     inspector.view = view
#
#     operation = inspector.get_operation(path, method)
#     assert 'responses' in operation
#     assert '200' in operation['responses']
#     resp = operation['responses']['200']['content']
#     data = resp['application/vnd.api+json']['schema']['properties']['data']
#     assert data['type'] == 'object'
#     assert data['required'] == ['type', 'id']
#     assert data['properties']['type'] == {'$ref': '#/components/schemas/type'}
