from django.db import models

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
