import pytest
from django.conf.urls import re_path
from rest_framework import status
from rest_framework.routers import SimpleRouter

from rest_framework_json_api.exceptions import Conflict
from rest_framework_json_api.relations import HyperlinkedRelatedField
from rest_framework_json_api.views import ModelViewSet, RelationshipView
from tests.models import BasicModel
from tests.serializers import (
    ForeignKeySourceSerializer,
    ManyToManySourceReadOnlySerializer,
    ManyToManySourceSerializer,
)


@pytest.mark.urls(__name__)
@pytest.mark.parametrize(
    "format_related_links,expected_url_segment",
    [
        (None, "relatedField_name"),
        ("dasherize", "related-field-name"),
        ("camelize", "relatedFieldName"),
        ("capitalize", "RelatedFieldName"),
        ("underscore", "related_field_name"),
    ],
)
def test_relationship_urls_respect_format_related_links_setting(
    settings, format_related_links, expected_url_segment
):
    settings.JSON_API_FORMAT_RELATED_LINKS = format_related_links

    model = BasicModel(text="Some text")

    field = HyperlinkedRelatedField(
        self_link_view_name="basic-model-relationships",
        related_link_view_name="basic-model-related",
        read_only=True,
    )
    field.field_name = "relatedField_name"

    expected = {
        "self": f"/basic_models/{model.pk}/relationships/{expected_url_segment}/",
        "related": f"/basic_models/{model.pk}/{expected_url_segment}/",
    }

    actual = field.get_links(model)

    assert expected == actual


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


# Routing setup


class BasicModelViewSet(ModelViewSet):
    class Meta:
        model = BasicModel


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
