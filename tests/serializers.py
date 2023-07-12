from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from tests.models import (
    BasicModel,
    ForeignKeySource,
    ForeignKeyTarget,
    ManyToManySource,
    ManyToManyTarget,
)


class BasicModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("text",)
        model = BasicModel


class ForeignKeySourceSerializer(serializers.ModelSerializer):
    target = ResourceRelatedField(queryset=ForeignKeyTarget.objects)

    class Meta:
        model = ForeignKeySource
        fields = ("target",)


class ManyToManySourceSerializer(serializers.ModelSerializer):
    targets = ResourceRelatedField(many=True, queryset=ManyToManyTarget.objects)

    class Meta:
        model = ManyToManySource
        fields = ("targets",)


class ManyToManyTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManyToManyTarget


class ManyToManySourceReadOnlySerializer(serializers.ModelSerializer):
    targets = ResourceRelatedField(many=True, read_only=True)

    class Meta:
        model = ManyToManySource
        fields = ("targets",)


class CallableDefaultSerializer(serializers.Serializer):
    field = serializers.CharField(default=serializers.CreateOnlyDefault("default"))

    class Meta:
        fields = ("field",)
