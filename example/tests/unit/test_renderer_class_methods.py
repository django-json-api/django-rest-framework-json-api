import pytest
from django.contrib.auth import get_user_model

from rest_framework_json_api import serializers
from rest_framework_json_api.renderers import JSONRenderer
from rest_framework_json_api.utils import get_serializer_fields

pytestmark = pytest.mark.django_db


class ResourceSerializer(serializers.ModelSerializer):
    version = serializers.SerializerMethodField()

    def get_version(self, obj):
        return "1.0.0"

    class Meta:
        fields = ("username",)
        meta_fields = ("version",)
        model = get_user_model()


def test_build_json_resource_obj():
    resource = {"username": "Alice", "version": "1.0.0"}

    serializer = ResourceSerializer(data={"username": "Alice"})
    serializer.is_valid()
    resource_instance = serializer.save()

    output = {
        "type": "user",
        "id": "1",
        "attributes": {"username": "Alice"},
        "meta": {"version": "1.0.0"},
    }

    assert (
        JSONRenderer.build_json_resource_obj(
            get_serializer_fields(serializer),
            resource,
            resource_instance,
            "user",
            serializer,
        )
        == output
    )


def test_can_override_methods():
    """
    Make sure extract_attributes and extract_relationships can be overriden.
    """

    resource = {"username": "Alice", "version": "1.0.0"}
    serializer = ResourceSerializer(data={"username": "Alice"})
    serializer.is_valid()
    resource_instance = serializer.save()

    output = {
        "type": "user",
        "id": "1",
        "attributes": {"username": "Alice"},
        "meta": {"version": "1.0.0"},
    }

    class CustomRenderer(JSONRenderer):
        extract_attributes_was_overriden = False
        extract_relationships_was_overriden = False

        @classmethod
        def extract_attributes(cls, fields, resource):
            cls.extract_attributes_was_overriden = True
            return super().extract_attributes(fields, resource)

        @classmethod
        def extract_relationships(cls, fields, resource, resource_instance):
            cls.extract_relationships_was_overriden = True
            return super().extract_relationships(fields, resource, resource_instance)

    assert (
        CustomRenderer.build_json_resource_obj(
            get_serializer_fields(serializer),
            resource,
            resource_instance,
            "user",
            serializer,
        )
        == output
    )
    assert CustomRenderer.extract_attributes_was_overriden
    assert CustomRenderer.extract_relationships_was_overriden


def test_extract_attributes():
    fields = {
        "id": serializers.Field(),
        "username": serializers.Field(),
        "deleted": serializers.ReadOnlyField(),
    }
    resource = {"id": 1, "deleted": None, "username": "jerel"}
    expected = {"username": "jerel", "deleted": None}
    assert sorted(JSONRenderer.extract_attributes(fields, resource)) == sorted(
        expected
    ), "Regular fields should be extracted"
    assert sorted(JSONRenderer.extract_attributes(fields, {})) == sorted(
        {"username": ""}
    ), "Should not extract read_only fields on empty serializer"


def test_extract_meta():
    serializer = ResourceSerializer(data={"username": "jerel", "version": "1.0.0"})
    serializer.is_valid()
    expected = {
        "version": "1.0.0",
    }
    assert JSONRenderer.extract_meta(serializer, serializer.data) == expected


class ExtractRootMetaResourceSerializer(ResourceSerializer):
    def get_root_meta(self, resource, many):
        if many:
            return {"foo": "meta-many-value"}
        else:
            return {"foo": "meta-value"}


class InvalidExtractRootMetaResourceSerializer(ResourceSerializer):
    def get_root_meta(self, resource, many):
        return "not a dict"


def test_extract_root_meta():
    serializer = ExtractRootMetaResourceSerializer()
    expected = {
        "foo": "meta-value",
    }
    assert JSONRenderer.extract_root_meta(serializer, {}) == expected


def test_extract_root_meta_many():
    serializer = ExtractRootMetaResourceSerializer(many=True)
    expected = {"foo": "meta-many-value"}
    assert JSONRenderer.extract_root_meta(serializer, {}) == expected


def test_extract_root_meta_invalid_meta():
    serializer = InvalidExtractRootMetaResourceSerializer()
    with pytest.raises(AssertionError):
        JSONRenderer.extract_root_meta(serializer, {})
