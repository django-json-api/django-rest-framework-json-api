import pytest
from django.urls import path, reverse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import SimpleRouter
from rest_framework.views import APIView

from rest_framework_json_api import serializers
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.renderers import JSONRenderer
from rest_framework_json_api.utils import format_link_segment
from rest_framework_json_api.views import ModelViewSet, ReadOnlyModelViewSet
from tests.models import BasicModel, ForeignKeySource
from tests.serializers import BasicModelSerializer, ForeignKeyTargetSerializer
from tests.views import (
    BasicModelViewSet,
    ForeignKeySourceViewSet,
    ManyToManySourceViewSet,
    NestedRelatedSourceViewSet,
)


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

    @pytest.mark.urls(__name__)
    def test_list(self, client, model):
        url = reverse("basic-model-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "data": [
                {
                    "type": "BasicModel",
                    "id": str(model.pk),
                    "attributes": {"text": "Model"},
                }
            ],
            "links": {
                "first": "http://testserver/basic_models/?page%5Bnumber%5D=1",
                "last": "http://testserver/basic_models/?page%5Bnumber%5D=1",
                "next": None,
                "prev": None,
            },
            "meta": {"pagination": {"count": 1, "page": 1, "pages": 1}},
        }

    @pytest.mark.urls(__name__)
    def test_list_with_include_foreign_key(self, client, foreign_key_source):
        url = reverse("foreign-key-source-list")
        response = client.get(url, data={"include": "target"})
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "included" in result
        assert [
            {
                "type": "ForeignKeyTarget",
                "id": str(foreign_key_source.target.pk),
                "attributes": {"name": foreign_key_source.target.name},
            }
        ] == result["included"]

    @pytest.mark.urls(__name__)
    def test_list_with_include_many_to_many_field(
        self, client, many_to_many_source, many_to_many_targets
    ):
        url = reverse("many-to-many-source-list")
        response = client.get(url, data={"include": "targets"})
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "included" in result
        assert [
            {
                "type": "ManyToManyTarget",
                "id": str(target.pk),
                "attributes": {"name": target.name},
            }
            for target in many_to_many_targets
        ] == result["included"]

    @pytest.mark.urls(__name__)
    def test_list_with_include_nested_related_field(
        self, client, nested_related_source, many_to_many_sources, many_to_many_targets
    ):
        url = reverse("nested-related-source-list")
        response = client.get(url, data={"include": "m2m_sources,m2m_sources.targets"})
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "included" in result

        assert [
            {
                "type": "ManyToManySource",
                "id": str(source.pk),
                "relationships": {
                    "targets": {
                        "data": [
                            {"id": str(target.pk), "type": "ManyToManyTarget"}
                            for target in source.targets.all()
                        ],
                        "meta": {"count": source.targets.count()},
                    }
                },
            }
            for source in many_to_many_sources
        ] + [
            {
                "type": "ManyToManyTarget",
                "id": str(target.pk),
                "attributes": {"name": target.name},
            }
            for target in many_to_many_targets
        ] == result[
            "included"
        ]

    @pytest.mark.urls(__name__)
    def test_list_with_invalid_include(self, client, foreign_key_source):
        url = reverse("foreign-key-source-list")
        response = client.get(url, data={"include": "invalid"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        result = response.json()
        assert (
            result["errors"][0]["detail"]
            == "This endpoint does not support the include parameter for path invalid"
        )

    @pytest.mark.urls(__name__)
    def test_list_with_default_included_resources(self, client, foreign_key_source):
        url = reverse("default-included-resources-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "included" in result
        assert [
            {
                "type": "ForeignKeyTarget",
                "id": str(foreign_key_source.target.pk),
                "attributes": {"name": foreign_key_source.target.name},
            }
        ] == result["included"]

    @pytest.mark.urls(__name__)
    def test_retrieve(self, client, model):
        url = reverse("basic-model-detail", kwargs={"pk": model.pk})
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "data": {
                "type": "BasicModel",
                "id": str(model.pk),
                "attributes": {"text": "Model"},
            }
        }

    @pytest.mark.urls(__name__)
    def test_retrieve_with_include_foreign_key(self, client, foreign_key_source):
        url = reverse("foreign-key-source-detail", kwargs={"pk": foreign_key_source.pk})
        response = client.get(url, data={"include": "target"})
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert "included" in result
        assert [
            {
                "type": "ForeignKeyTarget",
                "id": str(foreign_key_source.target.pk),
                "attributes": {"name": foreign_key_source.target.name},
            }
        ] == result["included"]

    @pytest.mark.urls(__name__)
    def test_patch(self, client, model):
        data = {
            "data": {
                "id": str(model.pk),
                "type": "BasicModel",
                "attributes": {"text": "changed"},
            }
        }

        url = reverse("basic-model-detail", kwargs={"pk": model.pk})
        response = client.patch(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "data": {
                "type": "BasicModel",
                "id": str(model.pk),
                "attributes": {"text": "changed"},
            }
        }

    @pytest.mark.urls(__name__)
    def test_delete(self, client, model):
        url = reverse("basic-model-detail", kwargs={"pk": model.pk})
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert BasicModel.objects.count() == 0
        assert len(response.rendered_content) == 0

    @pytest.mark.urls(__name__)
    def test_create_with_sparse_fields(self, client, foreign_key_target):
        url = reverse("foreign-key-source-list")
        data = {
            "data": {
                "id": None,
                "type": "ForeignKeySource",
                "attributes": {"name": "Test"},
                "relationships": {
                    "target": {
                        "data": {
                            "id": str(foreign_key_target.pk),
                            "type": "ForeignKeyTarget",
                        }
                    }
                },
            }
        }
        response = client.post(f"{url}?fields[ForeignKeySource]=target", data=data)
        assert response.status_code == status.HTTP_201_CREATED
        foreign_key_source = ForeignKeySource.objects.first()
        assert foreign_key_source.name == "Test"
        assert response.json() == {
            "data": {
                "id": str(foreign_key_source.pk),
                "type": "ForeignKeySource",
                "relationships": {
                    "target": {
                        "data": {
                            "id": str(foreign_key_target.pk),
                            "type": "ForeignKeyTarget",
                        }
                    }
                },
            }
        }


class TestReadonlyModelViewSet:
    @pytest.mark.parametrize(
        "method",
        ["get", "post", "patch", "delete"],
    )
    @pytest.mark.parametrize(
        "custom_action,action_kwargs",
        [("list_action", {}), ("detail_action", {"pk": 1})],
    )
    def test_custom_action_allows_all_methods(
        self, rf, method, custom_action, action_kwargs
    ):
        """
        Test that write methods are allowed on custom list actions.

        Even though a read only view only allows reading, custom actions
        should be allowed to define other methods which are allowed.
        """

        class ReadOnlyModelViewSetWithCustomActions(ReadOnlyModelViewSet):
            serializer_class = BasicModelSerializer
            queryset = BasicModel.objects.all()

            @action(detail=False, methods=["get", "post", "patch", "delete"])
            def list_action(self, request):
                return Response(status=status.HTTP_204_NO_CONTENT)

            @action(detail=True, methods=["get", "post", "patch", "delete"])
            def detail_action(self, request, pk):
                return Response(status=status.HTTP_204_NO_CONTENT)

        view = ReadOnlyModelViewSetWithCustomActions.as_view({method: custom_action})
        request = getattr(rf, method)("/", data={})
        response = view(request, **action_kwargs)
        assert response.status_code == status.HTTP_204_NO_CONTENT


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
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "data": {
                "type": "custom",
                "id": "123",
                "attributes": {"body": "hello"},
            }
        }

    @pytest.mark.urls(__name__)
    def test_post_with_missing_id(self, client):
        data = {
            "data": {
                "id": None,
                "type": "custom",
                "attributes": {"body": "hello"},
            }
        }

        url = reverse("custom")

        response = client.post(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "data": {
                "type": "custom",
                "id": None,
                "attributes": {"body": "hello"},
            }
        }

    @pytest.mark.urls(__name__)
    def test_patch_with_custom_id(self, client):
        data = {
            "data": {
                "id": 2_193_102,
                "type": "custom",
                "attributes": {"body": "hello"},
            }
        }

        url = reverse("custom-id")

        response = client.patch(url, data=data)
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "data": {
                "type": "custom",
                "id": "2176ce",  # get_id() -> hex
                "attributes": {"body": "hello"},
            }
        }


# Routing setup


class DefaultIncludedResourcesSerializer(serializers.ModelSerializer):
    included_serializers = {"target": ForeignKeyTargetSerializer}

    class Meta:
        model = ForeignKeySource
        fields = ("target",)

    class JSONAPIMeta:
        included_resources = ["target"]


class DefaultIncludedResourcesViewSet(ModelViewSet):
    serializer_class = DefaultIncludedResourcesSerializer
    queryset = ForeignKeySource.objects.all()
    ordering = ["id"]


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


class CustomIdModelSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    body = serializers.CharField()

    def get_id(self, obj):
        return hex(obj.id)[2:]


class CustomAPIView(APIView):
    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]
    resource_name = "custom"

    def patch(self, request, *args, **kwargs):
        serializer = CustomModelSerializer(CustomModel(request.data))
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    def post(self, request, *args, **kwargs):
        serializer = CustomModelSerializer(request.data)
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class CustomIdAPIView(APIView):
    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]
    resource_name = "custom"

    def patch(self, request, *args, **kwargs):
        serializer = CustomIdModelSerializer(CustomModel(request.data))
        return Response(status=status.HTTP_200_OK, data=serializer.data)


router = SimpleRouter()
router.register(r"basic_models", BasicModelViewSet, basename="basic-model")
router.register(
    r"foreign_key_sources", ForeignKeySourceViewSet, basename="foreign-key-source"
)
router.register(
    r"many_to_many_sources", ManyToManySourceViewSet, basename="many-to-many-source"
)
router.register(
    r"nested_related_sources",
    NestedRelatedSourceViewSet,
    basename="nested-related-source",
)
router.register(
    r"default_included_resources",
    DefaultIncludedResourcesViewSet,
    basename="default-included-resources",
)

urlpatterns = [
    path("custom", CustomAPIView.as_view(), name="custom"),
    path("custom-id", CustomIdAPIView.as_view(), name="custom-id"),
]
urlpatterns += router.urls
