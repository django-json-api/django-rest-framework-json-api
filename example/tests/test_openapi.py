# largely based on DRF's test_openapi
import json

from django.conf.urls import url
from django.test import RequestFactory, override_settings
from rest_framework.request import Request

from rest_framework_json_api.management.commands.generateschema import Command
from rest_framework_json_api.schemas.openapi import AutoSchema, SchemaGenerator

from example import views
from example.tests import TestBase


def create_request(path):
    factory = RequestFactory()
    request = Request(factory.get(path))
    return request


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


def test_generateschema_command():
    command = Command()
    assert command.get_generator_class() == SchemaGenerator


class TestSchemaRelatedField(TestBase):
    def test_schema_related_serializers(self):
        """
        Confirm that paths are generated for related fields. For example:
        url path '/authors/{pk}/{related_field>}/' generates:
            /authors/{id}/relationships/comments/
            /authors/{id}/relationships/entries/
            /authors/{id}/relationships/first_entry/ -- Maybe?
            /authors/{id}/comments/
            /authors/{id}/entries/
            /authors/{id}/first_entry/
        and confirm that the schema for the related field is properly rendered
        """
        generator = SchemaGenerator()
        request = create_request('/')
        schema = generator.get_schema(request=request)
        # make sure the path's relationship and related {related_field}'s got expanded
        assert '/authors/{id}/relationships/entries' in schema['paths']
        assert '/authors/{id}/relationships/comments' in schema['paths']
        # first_entry is a special case (SerializerMethodRelatedField)
        # TODO: '/authors/{id}/relationships/first_entry' supposed to be there?
        # It fails when doing the actual GET, so this schema excluding it is OK.
        # assert '/authors/{id}/relationships/first_entry/' in schema['paths']
        assert '/authors/{id}/comments/' in schema['paths']
        assert '/authors/{id}/entries/' in schema['paths']
        assert '/authors/{id}/first_entry/' in schema['paths']
        first_get = schema['paths']['/authors/{id}/first_entry/']['get']['responses']['200']
        first_schema = first_get['content']['application/vnd.api+json']['schema']
        first_props = first_schema['properties']['data']['properties']['attributes']['properties']
        assert 'headline' in first_props
        assert first_props['headline'] == {'type': 'string', 'maxLength': 255}
