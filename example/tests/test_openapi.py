# largely based on DRF's test_openapi
import json

from django.test import RequestFactory, override_settings
from django.urls import re_path
from rest_framework.request import Request

from rest_framework_json_api.schemas.openapi import AutoSchema, SchemaGenerator

from example import views


def create_request(path):
    factory = RequestFactory()
    request = Request(factory.get(path))
    return request


def create_view_with_kw(view_cls, method, request, initkwargs):
    generator = SchemaGenerator()
    view = generator.create_view(view_cls.as_view(initkwargs), method, request)
    return view


def test_path_without_parameters(snapshot):
    path = "/authors/"
    method = "GET"

    view = create_view_with_kw(
        views.AuthorViewSet, method, create_request(path), {"get": "list"}
    )
    inspector = AutoSchema()
    inspector.view = view

    operation = inspector.get_operation(path, method)
    assert snapshot == json.dumps(operation, indent=2, sort_keys=True)


def test_path_with_id_parameter(snapshot):
    path = "/authors/{id}/"
    method = "GET"

    view = create_view_with_kw(
        views.AuthorViewSet, method, create_request(path), {"get": "retrieve"}
    )
    inspector = AutoSchema()
    inspector.view = view

    operation = inspector.get_operation(path, method)
    assert snapshot == json.dumps(operation, indent=2, sort_keys=True)


def test_post_request(snapshot):
    method = "POST"
    path = "/authors/"

    view = create_view_with_kw(
        views.AuthorViewSet, method, create_request(path), {"post": "create"}
    )
    inspector = AutoSchema()
    inspector.view = view

    operation = inspector.get_operation(path, method)
    assert snapshot == json.dumps(operation, indent=2, sort_keys=True)


def test_patch_request(snapshot):
    method = "PATCH"
    path = "/authors/{id}"

    view = create_view_with_kw(
        views.AuthorViewSet, method, create_request(path), {"patch": "update"}
    )
    inspector = AutoSchema()
    inspector.view = view

    operation = inspector.get_operation(path, method)
    assert snapshot == json.dumps(operation, indent=2, sort_keys=True)


def test_delete_request(snapshot):
    method = "DELETE"
    path = "/authors/{id}"

    view = create_view_with_kw(
        views.AuthorViewSet, method, create_request(path), {"delete": "delete"}
    )
    inspector = AutoSchema()
    inspector.view = view

    operation = inspector.get_operation(path, method)
    assert snapshot == json.dumps(operation, indent=2, sort_keys=True)


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_SCHEMA_CLASS": "rest_framework_json_api.schemas.openapi.AutoSchema"
    }
)
def test_schema_construction(snapshot):
    """Construction of the top level dictionary."""
    patterns = [
        re_path("^authors/?$", views.AuthorViewSet.as_view({"get": "list"})),
    ]
    generator = SchemaGenerator(patterns=patterns)

    request = create_request("/")
    schema = generator.get_schema(request=request)

    assert snapshot == json.dumps(schema, indent=2, sort_keys=True)


def test_schema_id_field():
    """ID field is only included in the root, not the attributes."""
    patterns = [
        re_path("^companies/?$", views.CompanyViewset.as_view({"get": "list"})),
    ]
    generator = SchemaGenerator(patterns=patterns)

    request = create_request("/")
    schema = generator.get_schema(request=request)

    company_properties = schema["components"]["schemas"]["Company"]["properties"]
    assert company_properties["id"] == {"$ref": "#/components/schemas/id"}
    assert "id" not in company_properties["attributes"]["properties"]


def test_schema_subserializers():
    """Schema for child Serializers reflects the actual response structure."""
    patterns = [
        re_path(
            "^questionnaires/?$", views.QuestionnaireViewset.as_view({"get": "list"})
        ),
    ]
    generator = SchemaGenerator(patterns=patterns)

    request = create_request("/")
    schema = generator.get_schema(request=request)

    assert {
        "type": "object",
        "properties": {
            "metadata": {
                "type": "object",
                "properties": {
                    "author": {"type": "string"},
                    "producer": {"type": "string"},
                },
                "required": ["author"],
            },
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "required": {"type": "boolean", "default": False},
                    },
                    "required": ["text"],
                },
            },
            "name": {"type": "string", "maxLength": 100},
        },
        "required": ["name", "questions", "metadata"],
    } == schema["components"]["schemas"]["Questionnaire"]["properties"]["attributes"]


def test_schema_parameters_include():
    """Include paramater is only used when serializer defines included_serializers."""
    patterns = [
        re_path("^authors/?$", views.AuthorViewSet.as_view({"get": "list"})),
        re_path("^project-types/?$", views.ProjectTypeViewset.as_view({"get": "list"})),
    ]
    generator = SchemaGenerator(patterns=patterns)

    request = create_request("/")
    schema = generator.get_schema(request=request)

    include_ref = {"$ref": "#/components/parameters/include"}
    assert include_ref in schema["paths"]["/authors/"]["get"]["parameters"]
    assert include_ref not in schema["paths"]["/project-types/"]["get"]["parameters"]


def test_schema_serializer_method_resource_related_field():
    """SerializerMethodResourceRelatedField fieds have the correct relation ref."""
    patterns = [
        re_path("^entries/?$", views.EntryViewSet.as_view({"get": "list"})),
    ]
    generator = SchemaGenerator(patterns=patterns)

    request = Request(RequestFactory().get("/", {"include": "featured"}))
    schema = generator.get_schema(request=request)

    entry_schema = schema["components"]["schemas"]["Entry"]
    entry_relationships = entry_schema["properties"]["relationships"]["properties"]

    rel_to_many_ref = {"$ref": "#/components/schemas/reltomany"}
    assert entry_relationships["suggested"] == rel_to_many_ref
    assert entry_relationships["suggestedHyperlinked"] == rel_to_many_ref

    rel_to_one_ref = {"$ref": "#/components/schemas/reltoone"}
    assert entry_relationships["featured"] == rel_to_one_ref
    assert entry_relationships["featuredHyperlinked"] == rel_to_one_ref


def test_schema_related_serializers():
    """
    Confirm that paths are generated for related fields. For example:
        /authors/{pk}/{related_field>}
        /authors/{id}/comments/
        /authors/{id}/entries/
        /authors/{id}/first_entry/
    and confirm that the schema for the related field is properly rendered
    """
    generator = SchemaGenerator()
    request = create_request("/")
    schema = generator.get_schema(request=request)
    # make sure the path's relationship and related {related_field}'s got expanded
    assert "/authors/{id}/relationships/{related_field}" in schema["paths"]
    assert "/authors/{id}/comments/" in schema["paths"]
    assert "/authors/{id}/entries/" in schema["paths"]
    assert "/authors/{id}/first_entry/" in schema["paths"]
    first_get = schema["paths"]["/authors/{id}/first_entry/"]["get"]["responses"]["200"]
    first_schema = first_get["content"]["application/vnd.api+json"]["schema"]
    first_props = first_schema["properties"]["data"]
    assert "$ref" in first_props
    assert first_props["$ref"] == "#/components/schemas/Entry"
