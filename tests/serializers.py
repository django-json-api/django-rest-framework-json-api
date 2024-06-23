from rest_framework.settings import api_settings

from rest_framework_json_api import serializers
from tests.models import (
    BasicModel,
    ForeignKeySource,
    ForeignKeyTarget,
    ManyToManySource,
    ManyToManyTarget,
    NestedRelatedSource,
    URLModel,
)


class BasicModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("text",)
        model = BasicModel


class URLModelSerializer(serializers.ModelSerializer):
    class Meta:
        fields = (
            "text",
            "url",
        )
        model = URLModel


class ForeignKeyTargetSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("name",)
        model = ForeignKeyTarget


class ForeignKeySourceSerializer(serializers.ModelSerializer):
    included_serializers = {"target": ForeignKeyTargetSerializer}

    class Meta:
        model = ForeignKeySource
        fields = (
            "name",
            "target",
        )


class ForeignKeySourcetHyperlinkedSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ForeignKeySource
        fields = (
            "name",
            "target",
            api_settings.URL_FIELD_NAME,
        )


class ManyToManyTargetSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("name",)
        model = ManyToManyTarget


class ManyToManySourceSerializer(serializers.ModelSerializer):
    included_serializers = {"targets": "tests.serializers.ManyToManyTargetSerializer"}

    class Meta:
        model = ManyToManySource
        fields = ("targets",)


class ManyToManySourceReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = ManyToManySource
        fields = ("targets",)


class NestedRelatedSourceSerializer(serializers.ModelSerializer):
    included_serializers = {
        "m2m_sources": ManyToManySourceSerializer,
        "fk_source": ForeignKeySourceSerializer,
        "m2m_targets": ManyToManyTargetSerializer,
        "fk_target": ForeignKeyTargetSerializer,
    }

    class Meta:
        model = NestedRelatedSource
        fields = ("m2m_sources", "fk_source", "m2m_targets", "fk_target")


class CallableDefaultSerializer(serializers.Serializer):
    field = serializers.CharField(default=serializers.CreateOnlyDefault("default"))

    class Meta:
        fields = ("field",)
