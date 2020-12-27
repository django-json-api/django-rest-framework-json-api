import pytest

from rest_framework_json_api import serializers, views
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.utils import format_value

from .models import BasicModel

related_model_field_name = "related_field_model"


@pytest.mark.parametrize(
    "format_links",
    [
        None,
        "dasherize",
        "camelize",
        "capitalize",
        "underscore",
    ],
)
def test_get_related_field_name_handles_formatted_link_segments(format_links, rf):
    url_segment = format_value(related_model_field_name, format_links)

    request = rf.get(f"/basic_models/1/{url_segment}")

    view = BasicModelFakeViewSet()
    view.setup(request, related_field=url_segment)

    assert view.get_related_field_name() == related_model_field_name


class BasicModelSerializer(serializers.ModelSerializer):
    related_model_field = ResourceRelatedField(queryset=BasicModel.objects)

    def __init__(self, *args, **kwargs):
        # Intentionally setting field_name property to something that matches no format
        self.related_model_field.field_name = related_model_field_name
        super(BasicModelSerializer, self).__init(*args, **kwargs)

    class Meta:
        model = BasicModel


class BasicModelFakeViewSet(views.ModelViewSet):
    serializer_class = BasicModelSerializer

    def retrieve(self, request, *args, **kwargs):
        pass
