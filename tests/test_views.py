import pytest
from django.urls import path, reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_json_api import serializers
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.renderers import JSONRenderer
from rest_framework_json_api.utils import format_link_segment
from rest_framework_json_api.views import ModelViewSet
from tests.models import BasicModel


class TestModelViewSet:
    @pytest.mark.parametrize(
        "format_links",
        [
            False,
            "dasherize",
            "camelize",
            "capitalize",
            "underscore",
        ],
    )
    def test_get_related_field_name_handles_formatted_link_segments(
        self, settings, format_links, rf
    ):
        settings.JSON_API_FORMAT_RELATED_LINKS = format_links

        # use field name which actually gets formatted
        related_model_field_name = "related_field_model"

        class RelatedFieldNameSerializer(serializers.ModelSerializer):
            related_model_field = ResourceRelatedField(queryset=BasicModel.objects)

            def __init__(self, *args, **kwargs):
                self.related_model_field.field_name = related_model_field_name
                super().__init(*args, **kwargs)

            class Meta:
                model = BasicModel

        class RelatedFieldNameView(ModelViewSet):
            serializer_class = RelatedFieldNameSerializer

        url_segment = format_link_segment(related_model_field_name)

        request = rf.get(f"/basic_models/1/{url_segment}")

        view = RelatedFieldNameView()
        view.setup(request, related_field=url_segment)

        assert view.get_related_field_name() == related_model_field_name


class TestAPIView:
    @pytest.mark.urls(__name__)
    def test_patch(self, client):
        data = {
            "data": {
                "id": 123,
                "type": "custom",
                "attributes": {"body": "hello"},
            }
        }

        url = reverse("custom")

        response = client.patch(url, data=data)
        result = response.json()

        assert result["data"]["id"] == str(123)
        assert result["data"]["type"] == "custom"
        assert result["data"]["attributes"]["body"] == "hello"


class CustomModel:
    def __init__(self, response_dict):
        for k, v in response_dict.items():
            setattr(self, k, v)

    @property
    def pk(self):
        return self.id if hasattr(self, "id") else None


class CustomModelSerializer(serializers.Serializer):
    body = serializers.CharField()
    id = serializers.IntegerField()


class CustomAPIView(APIView):
    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]
    resource_name = "custom"

    def patch(self, request, *args, **kwargs):
        serializer = CustomModelSerializer(CustomModel(request.data))
        return Response(status=status.HTTP_200_OK, data=serializer.data)


urlpatterns = [
    path("custom", CustomAPIView.as_view(), name="custom"),
]
