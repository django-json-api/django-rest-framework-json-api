import pytest
from django.urls import re_path
from rest_framework import status
from rest_framework.fields import SkipField
from rest_framework.routers import SimpleRouter
from rest_framework.serializers import Serializer

from rest_framework_json_api.exceptions import Conflict
from rest_framework_json_api.relations import (
    HyperlinkedRelatedField,
    SerializerMethodHyperlinkedRelatedField,
)
from rest_framework_json_api.utils import format_link_segment
from rest_framework_json_api.views import RelationshipView
from tests.models import BasicModel
from tests.serializers import (
    ForeignKeySourceSerializer,
    ManyToManySourceReadOnlySerializer,
    ManyToManySourceSerializer,
)
from tests.views import BasicModelViewSet


@pytest.mark.django_db
class TestResourceRelatedField:
    @pytest.mark.parametrize(
        "format_type,pluralize_type,resource_type",
        [
            (False, False, "ForeignKeyTarget"),
            (False, True, "ForeignKeyTargets"),
            ("dasherize", False, "foreign-key-target"),
            ("dasherize", True, "foreign-key-targets"),
        ],
    )
    def test_serialize(
        self, format_type, pluralize_type, resource_type, foreign_key_target, settings
    ):
        settings.JSON_API_FORMAT_TYPES = format_type
        settings.JSON_API_PLURALIZE_TYPES = pluralize_type

        serializer = ForeignKeySourceSerializer(instance={"target": foreign_key_target})
        expected = {
            "type": resource_type,
            "id": str(foreign_key_target.pk),
        }

        assert serializer.data["target"] == expected

    @pytest.mark.parametrize(
        "format_type,pluralize_type,resource_type",
        [
            (False, False, "ForeignKeyTarget"),
            (False, True, "ForeignKeyTargets"),
            ("dasherize", False, "foreign-key-target"),
            ("dasherize", True, "foreign-key-targets"),
        ],
    )
    def test_deserialize(
        self, format_type, pluralize_type, resource_type, foreign_key_target, settings
    ):
        settings.JSON_API_FORMAT_TYPES = format_type
        settings.JSON_API_PLURALIZE_TYPES = pluralize_type

        serializer = ForeignKeySourceSerializer(
            data={"target": {"type": resource_type, "id": str(foreign_key_target.pk)}}
        )

        assert serializer.is_valid()
        assert serializer.validated_data["target"] == foreign_key_target

    @pytest.mark.parametrize(
        "format_type,pluralize_type,resource_type",
        [
            (False, False, "ForeignKeyTargets"),
            (False, False, "Invalid"),
            (False, False, "foreign-key-target"),
            (False, True, "ForeignKeyTarget"),
            ("dasherize", False, "ForeignKeyTarget"),
            ("dasherize", True, "ForeignKeyTargets"),
        ],
    )
    def test_validation_fails_on_invalid_type(
        self, format_type, pluralize_type, resource_type, foreign_key_target, settings
    ):
        settings.JSON_API_FORMAT_TYPES = format_type
        settings.JSON_API_PLURALIZE_TYPES = pluralize_type

        with pytest.raises(Conflict) as e:
            serializer = ForeignKeySourceSerializer(
                data={
                    "target": {"type": resource_type, "id": str(foreign_key_target.pk)}
                }
            )
            serializer.is_valid()
        assert e.value.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.parametrize(
        "format_type,pluralize_type,resource_type",
        [
            (False, False, "ManyToManyTarget"),
            (False, True, "ManyToManyTargets"),
            ("dasherize", False, "many-to-many-target"),
            ("dasherize", True, "many-to-many-targets"),
        ],
    )
    def test_serialize_many_to_many_relation(
        self,
        format_type,
        pluralize_type,
        resource_type,
        many_to_many_source,
        many_to_many_targets,
        settings,
    ):
        settings.JSON_API_FORMAT_TYPES = format_type
        settings.JSON_API_PLURALIZE_TYPES = pluralize_type

        serializer = ManyToManySourceSerializer(instance=many_to_many_source)
        expected = [
            {"type": resource_type, "id": str(target.pk)}
            for target in many_to_many_targets
        ]
        assert serializer.data["targets"] == expected

    @pytest.mark.parametrize(
        "format_type,pluralize_type,resource_type",
        [
            (False, False, "ManyToManyTarget"),
            (False, True, "ManyToManyTargets"),
            ("dasherize", False, "many-to-many-target"),
            ("dasherize", True, "many-to-many-targets"),
        ],
    )
    @pytest.mark.parametrize(
        "serializer_class",
        [ManyToManySourceSerializer, ManyToManySourceReadOnlySerializer],
    )
    def test_deserialize_many_to_many_relation(
        self,
        format_type,
        pluralize_type,
        resource_type,
        serializer_class,
        many_to_many_targets,
        settings,
    ):
        settings.JSON_API_FORMAT_TYPES = format_type
        settings.JSON_API_PLURALIZE_TYPES = pluralize_type

        targets = [
            {"type": resource_type, "id": target.pk} for target in many_to_many_targets
        ]
        serializer = ManyToManySourceSerializer(data={"targets": targets})
        assert serializer.is_valid()
        assert serializer.validated_data["targets"] == many_to_many_targets

    @pytest.mark.parametrize(
        "resource_identifier,error",
        [
            (
                {"type": "ForeignKeyTarget"},
                "Invalid resource identifier object: missing 'id' attribute",
            ),
            (
                {"id": "1234"},
                "Invalid resource identifier object: missing 'type' attribute",
            ),
        ],
    )
    def test_invalid_resource_id_object(self, resource_identifier, error):
        serializer = ForeignKeySourceSerializer(data={"target": resource_identifier})
        assert not serializer.is_valid()
        assert serializer.errors == {"target": [error]}


class TestHyperlinkedRelatedField:
    @pytest.fixture
    def instance(self):
        # dummy instance
        return object()

    @pytest.fixture
    def serializer(self):
        class HyperlinkedRelatedFieldSerializer(Serializer):
            single = HyperlinkedRelatedField(
                self_link_view_name="basic-model-relationships",
                related_link_view_name="basic-model-related",
                read_only=True,
            )
            many = HyperlinkedRelatedField(
                self_link_view_name="basic-model-relationships",
                related_link_view_name="basic-model-related",
                read_only=True,
                many=True,
            )
            single_serializer_method = SerializerMethodHyperlinkedRelatedField(
                self_link_view_name="basic-model-relationships",
                related_link_view_name="basic-model-related",
                read_only=True,
            )
            many_serializer_method = SerializerMethodHyperlinkedRelatedField(
                self_link_view_name="basic-model-relationships",
                related_link_view_name="basic-model-related",
                read_only=True,
                many=True,
            )

            def get_single_serializer_method(self, obj):  # pragma: no cover
                raise NotImplementedError

            def get_many_serializer_method(self, obj):  # pragma: no cover
                raise NotImplementedError

        return HyperlinkedRelatedFieldSerializer()

    @pytest.fixture(
        params=["single", "many", "single_serializer_method", "many_serializer_method"]
    )
    def field(self, serializer, request):
        field = serializer.fields[request.param]
        field.field_name = request.param
        return field

    def test_get_attribute(self, model, field):
        with pytest.raises(SkipField):
            field.get_attribute(model)

    def test_to_representation(self, model, field):
        with pytest.raises(NotImplementedError):
            field.to_representation(model)

    @pytest.mark.urls(__name__)
    @pytest.mark.parametrize(
        "format_related_links",
        [
            False,
            "dasherize",
            "camelize",
            "capitalize",
            "underscore",
        ],
    )
    def test_get_links(
        self,
        format_related_links,
        field,
        settings,
        model,
    ):
        settings.JSON_API_FORMAT_RELATED_LINKS = format_related_links

        link_segment = format_link_segment(field.field_name)

        expected = {
            "self": f"/basic_models/{model.pk}/relationships/{link_segment}/",
            "related": f"/basic_models/{model.pk}/{link_segment}/",
        }

        if hasattr(field, "child_relation"):
            # many case
            field = field.child_relation

        actual = field.get_links(model)
        assert expected == actual


# Routing setup


class BasicModelRelationshipView(RelationshipView):
    queryset = BasicModel.objects


router = SimpleRouter()
router.register(r"basic_models", BasicModelViewSet, basename="basic-model")

urlpatterns = [
    re_path(
        r"^basic_models/(?P<pk>[^/.]+)/(?P<related_field>[^/.]+)/$",
        BasicModelViewSet.as_view({"get": "retrieve_related"}),
        name="basic-model-related",
    ),
    re_path(
        r"^basic_models/(?P<pk>[^/.]+)/relationships/(?P<related_field>[^/.]+)/$",
        BasicModelRelationshipView.as_view(),
        name="basic-model-relationships",
    ),
]

urlpatterns += router.urls
