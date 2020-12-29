import pytest
from django.db import models
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_json_api import serializers
from rest_framework_json_api.utils import (
    format_field_names,
    format_link_segment,
    format_resource_type,
    format_value,
    get_included_serializers,
    get_related_resource_type,
    get_resource_name,
)
from tests.models import (
    BasicModel,
    DJAModel,
    ForeignKeySource,
    ForeignKeyTarget,
    ManyToManySource,
    ManyToManyTarget,
)


def test_get_resource_name_no_view():
    assert get_resource_name({}) is None


@pytest.mark.parametrize(
    "format_type,pluralize_type,output",
    [
        (False, False, "APIView"),
        (False, True, "APIViews"),
        ("dasherize", False, "api-view"),
        ("dasherize", True, "api-views"),
    ],
)
def test_get_resource_name_from_view(settings, format_type, pluralize_type, output):
    settings.JSON_API_FORMAT_TYPES = format_type
    settings.JSON_API_PLURALIZE_TYPES = pluralize_type

    view = APIView()
    context = {"view": view}
    assert output == get_resource_name(context)


@pytest.mark.parametrize(
    "format_type,pluralize_type",
    [
        (False, False),
        (False, True),
        ("dasherize", False),
        ("dasherize", True),
    ],
)
def test_get_resource_name_from_view_custom_resource_name(
    settings, format_type, pluralize_type
):
    settings.JSON_API_FORMAT_TYPES = format_type
    settings.JSON_API_PLURALIZE_TYPES = pluralize_type

    view = APIView()
    view.resource_name = "custom"
    context = {"view": view}
    assert "custom" == get_resource_name(context)


@pytest.mark.parametrize(
    "format_type,pluralize_type,output",
    [
        (False, False, "BasicModel"),
        (False, True, "BasicModels"),
        ("dasherize", False, "basic-model"),
        ("dasherize", True, "basic-models"),
    ],
)
def test_get_resource_name_from_model(settings, format_type, pluralize_type, output):
    settings.JSON_API_FORMAT_TYPES = format_type
    settings.JSON_API_PLURALIZE_TYPES = pluralize_type

    view = APIView()
    view.model = BasicModel
    context = {"view": view}
    assert output == get_resource_name(context)


@pytest.mark.parametrize(
    "format_type,pluralize_type,output",
    [
        (False, False, "BasicModel"),
        (False, True, "BasicModels"),
        ("dasherize", False, "basic-model"),
        ("dasherize", True, "basic-models"),
    ],
)
def test_get_resource_name_from_model_serializer_class(
    settings, format_type, pluralize_type, output
):
    class BasicModelSerializer(serializers.ModelSerializer):
        class Meta:
            fields = ("text",)
            model = BasicModel

    settings.JSON_API_FORMAT_TYPES = format_type
    settings.JSON_API_PLURALIZE_TYPES = pluralize_type

    view = GenericAPIView()
    view.serializer_class = BasicModelSerializer
    context = {"view": view}
    assert output == get_resource_name(context)


@pytest.mark.parametrize(
    "format_type,pluralize_type",
    [
        (False, False),
        (False, True),
        ("dasherize", False),
        ("dasherize", True),
    ],
)
def test_get_resource_name_from_model_serializer_class_custom_resource_name(
    settings, format_type, pluralize_type
):
    class BasicModelSerializer(serializers.ModelSerializer):
        class Meta:
            fields = ("text",)
            model = BasicModel

    settings.JSON_API_FORMAT_TYPES = format_type
    settings.JSON_API_PLURALIZE_TYPES = pluralize_type

    view = GenericAPIView()
    view.serializer_class = BasicModelSerializer
    view.serializer_class.Meta.resource_name = "custom"

    context = {"view": view}
    assert "custom" == get_resource_name(context)


@pytest.mark.parametrize(
    "format_type,pluralize_type",
    [
        (False, False),
        (False, True),
        ("dasherize", False),
        ("dasherize", True),
    ],
)
def test_get_resource_name_from_plain_serializer_class(
    settings, format_type, pluralize_type
):
    class PlainSerializer(serializers.Serializer):
        class Meta:
            resource_name = "custom"

    settings.JSON_API_FORMAT_TYPES = format_type
    settings.JSON_API_PLURALIZE_TYPES = pluralize_type

    view = GenericAPIView()
    view.serializer_class = PlainSerializer

    context = {"view": view}
    assert "custom" == get_resource_name(context)


@pytest.mark.parametrize(
    "status_code",
    [
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ],
)
def test_get_resource_name_with_errors(status_code):
    view = APIView()
    context = {"view": view}
    view.response = Response(status=status_code)
    assert "errors" == get_resource_name(context)


@pytest.mark.parametrize(
    "format_type,output",
    [
        ("camelize", {"fullName": {"last-name": "a", "first-name": "b"}}),
        ("capitalize", {"FullName": {"last-name": "a", "first-name": "b"}}),
        ("dasherize", {"full-name": {"last-name": "a", "first-name": "b"}}),
        ("underscore", {"full_name": {"last-name": "a", "first-name": "b"}}),
    ],
)
def test_format_field_names(settings, format_type, output):
    settings.JSON_API_FORMAT_FIELD_NAMES = format_type

    value = {"full_name": {"last-name": "a", "first-name": "b"}}
    assert format_field_names(value, format_type) == output


@pytest.mark.parametrize(
    "format_type,output",
    [
        (None, "first_Name"),
        ("camelize", "firstName"),
        ("capitalize", "FirstName"),
        ("dasherize", "first-name"),
        ("underscore", "first_name"),
    ],
)
def test_format_field_segment(settings, format_type, output):
    settings.JSON_API_FORMAT_RELATED_LINKS = format_type
    assert format_link_segment("first_Name") == output


@pytest.mark.parametrize(
    "format_type,output",
    [
        (None, "first_name"),
        ("camelize", "firstName"),
        ("capitalize", "FirstName"),
        ("dasherize", "first-name"),
        ("underscore", "first_name"),
    ],
)
def test_format_value(settings, format_type, output):
    assert format_value("first_name", format_type) == output


@pytest.mark.parametrize(
    "resource_type,pluralize,output",
    [
        (None, None, "ResourceType"),
        ("camelize", False, "resourceType"),
        ("camelize", True, "resourceTypes"),
    ],
)
def test_format_resource_type(settings, resource_type, pluralize, output):
    assert format_resource_type("ResourceType", resource_type, pluralize) == output


@pytest.mark.parametrize(
    "model_class,field,output",
    [
        (ManyToManySource, "targets", "ManyToManyTarget"),
        (ManyToManyTarget, "sources", "ManyToManySource"),
        (ForeignKeySource, "target", "ForeignKeyTarget"),
        (ForeignKeyTarget, "sources", "ForeignKeySource"),
    ],
)
def test_get_related_resource_type(model_class, field, output):
    class RelatedResourceTypeSerializer(serializers.ModelSerializer):
        class Meta:
            model = model_class
            fields = (field,)

    serializer = RelatedResourceTypeSerializer()
    field = serializer.fields[field]
    assert get_related_resource_type(field) == output


@pytest.mark.parametrize(
    "related_field_kwargs,output",
    [
        ({"queryset": BasicModel.objects}, "BasicModel"),
        ({"queryset": BasicModel.objects, "model": BasicModel}, "BasicModel"),
        ({"model": BasicModel, "read_only": True}, "BasicModel"),
    ],
)
def test_get_related_resource_type_from_plain_serializer_class(
    related_field_kwargs, output
):
    class PlainRelatedResourceTypeSerializer(serializers.Serializer):
        basic_models = serializers.ResourceRelatedField(
            many=True, **related_field_kwargs
        )

    serializer = PlainRelatedResourceTypeSerializer()
    field = serializer.fields["basic_models"]
    assert get_related_resource_type(field) == output


class ManyToManyTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManyToManyTarget


def test_get_included_serializers():
    class IncludedSerializersModel(DJAModel):
        self = models.ForeignKey("self", on_delete=models.CASCADE)
        target = models.ForeignKey(ManyToManyTarget, on_delete=models.CASCADE)
        other_target = models.ForeignKey(ManyToManyTarget, on_delete=models.CASCADE)

        class Meta:
            app_label = "tests"

    class IncludedSerializersSerializer(serializers.ModelSerializer):
        included_serializers = {
            "self": "self",
            "target": ManyToManyTargetSerializer,
            "other_target": "tests.test_utils.ManyToManyTargetSerializer",
        }

        class Meta:
            model = IncludedSerializersModel
            fields = ("self", "other_target", "target")

    included_serializers = get_included_serializers(IncludedSerializersSerializer)
    expected_included_serializers = {
        "self": IncludedSerializersSerializer,
        "target": ManyToManyTargetSerializer,
        "other_target": ManyToManyTargetSerializer,
    }

    assert included_serializers == expected_included_serializers
