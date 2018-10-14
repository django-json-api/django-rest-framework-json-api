import pytest
import factory

import json

from django.urls import reverse
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework import viewsets

from rest_framework_json_api.renderers import JSONRenderer

from example.models import Comment, Entry


# serializers
class RelatedModelSerializer(ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id',)


class DummyTestSerializer(ModelSerializer):
    """
    This serializer is a simple compound document serializer which includes only
    a single embedded relation
    """
    related_models = RelatedModelSerializer(source='comments', many=True, read_only=True)

    json_field = SerializerMethodField()

    def get_json_field(self, entry):
        return {'JsonKey': 'JsonValue'}

    class Meta:
        model = Entry
        fields = ('related_models', 'json_field')


# views
class DummyTestViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = DummyTestSerializer


def render_dummy_test_serialized_view(view_class):
    serializer = DummyTestSerializer(instance=Entry())
    renderer = JSONRenderer()
    return renderer.render(
        serializer.data,
        renderer_context={'view': view_class()})


# tests
def test_simple_reverse_relation_included_renderer():
    """
    Test renderer when a single reverse fk relation is passed.
    """
    rendered = render_dummy_test_serialized_view(
        DummyTestViewSet)

    assert rendered


def test_render_format_field_names(settings):
    """Test that json field is kept untouched."""
    settings.JSON_API_FORMAT_FIELD_NAMES = 'dasherize'
    rendered = render_dummy_test_serialized_view(DummyTestViewSet)

    result = json.loads(rendered.decode())
    assert result['data']['attributes']['json-field'] == {'JsonKey': 'JsonValue'}


def test_render_format_keys(settings):
    """Test that json field value keys are formated."""
    delattr(settings, 'JSON_API_FORMAT_FILED_NAMES')
    settings.JSON_API_FORMAT_KEYS = 'dasherize'
    rendered = render_dummy_test_serialized_view(DummyTestViewSet)

    result = json.loads(rendered.decode())
    assert result['data']['attributes']['json-field'] == {'json-key': 'JsonValue'}


@pytest.mark.django_db
def test_get_object_gives_correct_blog(client, blog, entry):

    url = reverse('drf-entry-blog', kwargs={'entry_pk': entry.id})
    resp = client.get(url)
    expected = {
        'data': {
            'attributes': {'name': blog.name},
            'id': '{}'.format(blog.id),
            'links': {'self': 'http://testserver/blogs/{}'.format(blog.id)},
            'meta': {'copyright': 2018},
            'relationships': {'tags': {'data': []}},
            'type': 'blogs'
        },
        'meta': {'apiDocs': '/docs/api/blogs'}
    }
    got = resp.json()
    assert got == expected


# @pytest.mark.django_db
# def test_get_object_updates_correct_blog(client, blog, entry):
#
#     url = reverse('drf-entry-blog', kwargs={'entry_pk': entry.id})
#     new_name = blog.name + " update"
#     assert not new_name == blog.name
#
#     resp = client.patch(url, {"name": new_name})
#     print(resp)
#
#     expected = {
#         'data': {
#             'attributes': {'name': new_name},
#             'id': '{}'.format(blog.id),
#             'links': {'self': 'http://testserver/blogs/{}'.format(blog.id)},
#             'meta': {'copyright': 2018},
#             'relationships': {'tags': {'data': []}},
#             'type': 'blogs'
#         },
#         'meta': {'apiDocs': '/docs/api/blogs'}
#     }
#     got = resp.json()
#     assert got == expected
