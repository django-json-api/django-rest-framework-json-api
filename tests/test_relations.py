import pytest
from django.conf.urls import re_path
from rest_framework.routers import SimpleRouter

from rest_framework_json_api.relations import HyperlinkedRelatedField
from rest_framework_json_api.views import ModelViewSet, RelationshipView

from .models import BasicModel


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
