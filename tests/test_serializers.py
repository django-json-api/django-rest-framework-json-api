import pytest
from django.db import models
from rest_framework.utils import model_meta

from rest_framework_json_api import serializers
from tests.models import DJAModel, ManyToManyTarget
from tests.serializers import ManyToManyTargetSerializer


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
            "other_target": "tests.serializers.ManyToManyTargetSerializer",
        }

        class Meta:
            model = IncludedSerializersModel
            fields = ("self", "other_target", "target")

    included_serializers = IncludedSerializersSerializer.included_serializers
    expected_included_serializers = {
        "self": IncludedSerializersSerializer,
        "target": ManyToManyTargetSerializer,
        "other_target": ManyToManyTargetSerializer,
    }

    assert included_serializers == expected_included_serializers


def test_reserved_field_names():
    with pytest.raises(AssertionError) as e:

        class ReservedFieldNamesSerializer(serializers.Serializer):
            meta = serializers.CharField()
            results = serializers.CharField()

        ReservedFieldNamesSerializer().fields

    assert str(e.value) == (
        "Serializer class tests.test_serializers.test_reserved_field_names.<locals>."
        "ReservedFieldNamesSerializer uses following reserved field name(s) which is "
        "not allowed: meta, results"
    )


def test_get_field_names():
    class MyTestModel(DJAModel):
        verified = models.BooleanField(default=False)
        uuid = models.UUIDField()

    class AnotherSerializer(serializers.Serializer):
        ref_id = serializers.CharField()
        reference_string = serializers.CharField()

    class MyTestModelSerializer(AnotherSerializer, serializers.ModelSerializer):
        an_extra_field = serializers.CharField()

        class Meta:
            model = MyTestModel
            fields = "__all__"
            extra_kwargs = {
                "verified": {"read_only": True},
            }

    # Same logic than in DRF get_fields() method
    declared_fields = MyTestModelSerializer._declared_fields
    info = model_meta.get_field_info(MyTestModel)

    assert MyTestModelSerializer().get_field_names(declared_fields, info) == [
        "id",
        "ref_id",
        "reference_string",
        "an_extra_field",
        "verified",
        "uuid",
    ]
