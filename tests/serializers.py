from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer
from tests.models import (
    BasicModel,
    ForeignKeySource,
    ForeignKeyTarget,
    ManyToManySource,
    ManyToManyTarget,
)


class BasicModelSerializer(ModelSerializer):
    class Meta:
        fields = ("text",)
        model = BasicModel


class ForeignKeySourceSerializer(ModelSerializer):
    target = ResourceRelatedField(queryset=ForeignKeyTarget.objects)

    class Meta:
        model = ForeignKeySource
        fields = ("target",)


class ManyToManySourceSerializer(ModelSerializer):
    targets = ResourceRelatedField(many=True, queryset=ManyToManyTarget.objects)

    class Meta:
        model = ManyToManySource
        fields = ("targets",)


class ManyToManyTargetSerializer(ModelSerializer):
    class Meta:
        model = ManyToManyTarget


class ManyToManySourceReadOnlySerializer(ModelSerializer):
    targets = ResourceRelatedField(many=True, read_only=True)

    class Meta:
        model = ManyToManySource
        fields = ("targets",)
