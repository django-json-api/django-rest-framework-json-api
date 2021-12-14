import json
from datetime import datetime

import pytest
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.serializers import ModelSerializer, SerializerMethodField

from rest_framework_json_api.renderers import JSONRenderer

from example.models import Blog, Comment, Entry


# serializers
class RelatedModelSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id",)


class DummyTestSerializer(ModelSerializer):
    """
    This serializer is a simple compound document serializer which includes only
    a single embedded relation
    """

    related_models = RelatedModelSerializer(
        source="comments", many=True, read_only=True
    )

    json_field = SerializerMethodField()

    def get_json_field(self, entry):
        return {"JsonKey": "JsonValue"}

    class Meta:
        model = Entry
        fields = ("related_models", "json_field")


# views
class DummyTestViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = DummyTestSerializer


def render_dummy_test_serialized_view(view_class):
    serializer = DummyTestSerializer(instance=Entry())
    renderer = JSONRenderer()
    return renderer.render(serializer.data, renderer_context={"view": view_class()})


# tests
def test_simple_reverse_relation_included_renderer():
    """
    Test renderer when a single reverse fk relation is passed.
    """
    rendered = render_dummy_test_serialized_view(DummyTestViewSet)

    assert rendered


def test_render_format_field_names(settings):
    """Test that json field is kept untouched."""
    settings.JSON_API_FORMAT_FIELD_NAMES = "dasherize"
    rendered = render_dummy_test_serialized_view(DummyTestViewSet)

    result = json.loads(rendered.decode())
    assert result["data"]["attributes"]["json-field"] == {"JsonKey": "JsonValue"}


@pytest.mark.django_db
def test_blog_create(client):

    url = reverse("drf-entry-blog-list")
    name = "Dummy Name"

    request_data = {
        "data": {"attributes": {"name": name}, "type": "blogs"},
    }

    resp = client.post(url, request_data)

    # look for created blog in database
    blog = Blog.objects.filter(name=name)

    # check if blog exists in database
    assert blog.count() == 1

    # get created blog from database
    blog = blog.first()

    expected = {
        "data": {
            "attributes": {"name": blog.name, "tags": []},
            "id": f"{blog.id}",
            "links": {"self": f"http://testserver/blogs/{blog.id}"},
            "meta": {"copyright": datetime.now().year},
            "type": "blogs",
        },
        "meta": {"apiDocs": "/docs/api/blogs"},
    }

    assert resp.status_code == 201
    assert resp.json() == expected


@pytest.mark.django_db
def test_get_object_gives_correct_blog(client, blog, entry):

    url = reverse("drf-entry-blog-detail", kwargs={"entry_pk": entry.id})
    resp = client.get(url)
    expected = {
        "data": {
            "attributes": {"name": blog.name, "tags": []},
            "id": f"{blog.id}",
            "links": {"self": f"http://testserver/blogs/{blog.id}"},
            "meta": {"copyright": datetime.now().year},
            "type": "blogs",
        },
        "meta": {"apiDocs": "/docs/api/blogs"},
    }
    got = resp.json()
    assert got == expected


@pytest.mark.django_db
def test_get_object_patches_correct_blog(client, blog, entry):

    url = reverse("drf-entry-blog-detail", kwargs={"entry_pk": entry.id})
    new_name = blog.name + " update"
    assert not new_name == blog.name

    request_data = {
        "data": {
            "attributes": {"name": new_name},
            "id": f"{blog.id}",
            "links": {"self": f"http://testserver/blogs/{blog.id}"},
            "meta": {"copyright": datetime.now().year},
            "relationships": {"tags": {"data": []}},
            "type": "blogs",
        },
        "meta": {"apiDocs": "/docs/api/blogs"},
    }

    resp = client.patch(url, data=request_data)

    assert resp.status_code == 200

    expected = {
        "data": {
            "attributes": {"name": new_name, "tags": []},
            "id": f"{blog.id}",
            "links": {"self": f"http://testserver/blogs/{blog.id}"},
            "meta": {"copyright": datetime.now().year},
            "type": "blogs",
        },
        "meta": {"apiDocs": "/docs/api/blogs"},
    }
    got = resp.json()
    assert got == expected


@pytest.mark.django_db
def test_get_object_deletes_correct_blog(client, entry):

    url = reverse("drf-entry-blog-detail", kwargs={"entry_pk": entry.id})

    resp = client.delete(url)

    assert resp.status_code == 204


@pytest.mark.django_db
def test_get_entry_list_with_blogs(client, entry):
    url = reverse("drf-entry-suggested", kwargs={"entry_pk": entry.id})
    resp = client.get(url)

    got = resp.json()

    expected = {
        "links": {
            "first": "http://testserver/drf-entries/1/suggested/?page%5Bnumber%5D=1",
            "last": "http://testserver/drf-entries/1/suggested/?page%5Bnumber%5D=1",
            "next": None,
            "prev": None,
        },
        "data": [
            {
                "type": "entries",
                "id": "1",
                "attributes": {
                    "tags": [],
                },
                "links": {"self": "http://testserver/drf-blogs/1"},
            }
        ],
        "meta": {"pagination": {"page": 1, "pages": 1, "count": 1}},
    }

    assert resp.status_code == 200
    assert got == expected
