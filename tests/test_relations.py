import pytest

from rest_framework_json_api.relations import HyperlinkedRelatedField

from .models import BasicModel


@pytest.mark.urls("tests.urls")
@pytest.mark.parametrize(
    "format_links,expected_url_segment",
    [
        (None, "relatedField_name"),
        ("dasherize", "related-field-name"),
        ("camelize", "relatedFieldName"),
        ("capitalize", "RelatedFieldName"),
        ("underscore", "related_field_name"),
    ],
)
def test_relationship_urls_respect_format_links(
    settings, format_links, expected_url_segment
):
    settings.JSON_API_FORMAT_LINKS = format_links

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
