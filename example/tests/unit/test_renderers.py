import json

import pytest

from rest_framework_json_api import serializers, views
from rest_framework_json_api.renderers import JSONRenderer

from example.models import Author, Comment, Entry


# serializers
class RelatedModelSerializer(serializers.ModelSerializer):
    blog = serializers.ReadOnlyField(source='entry.blog')

    class Meta:
        model = Comment
        fields = ('id', 'blog')


class DummyTestSerializer(serializers.ModelSerializer):
    '''
    This serializer is a simple compound document serializer which includes only
    a single embedded relation
    '''
    related_models = RelatedModelSerializer(
        source='comments', many=True, read_only=True)

    json_field = serializers.SerializerMethodField()

    def get_json_field(self, entry):
        return {'JsonKey': 'JsonValue'}

    class Meta:
        model = Entry
        fields = ('related_models', 'json_field')

    class JSONAPIMeta:
        included_resources = ('related_models',)


# views
class DummyTestViewSet(views.ModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = DummyTestSerializer


class ReadOnlyDummyTestViewSet(views.ReadOnlyModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = DummyTestSerializer


def render_dummy_test_serialized_view(view_class, instance):
    serializer = view_class.serializer_class(instance=instance)
    renderer = JSONRenderer()
    return renderer.render(
        serializer.data,
        renderer_context={'view': view_class()})


def test_simple_reverse_relation_included_renderer():
    '''
    Test renderer when a single reverse fk relation is passed.
    '''
    rendered = render_dummy_test_serialized_view(
        DummyTestViewSet, Entry())

    assert rendered


def test_simple_reverse_relation_included_read_only_viewset():
    rendered = render_dummy_test_serialized_view(
        ReadOnlyDummyTestViewSet, Entry())

    assert rendered


def test_render_format_field_names(settings):
    """Test that json field is kept untouched."""
    settings.JSON_API_FORMAT_FIELD_NAMES = 'dasherize'
    rendered = render_dummy_test_serialized_view(DummyTestViewSet, Entry())

    result = json.loads(rendered.decode())
    assert result['data']['attributes']['json-field'] == {'JsonKey': 'JsonValue'}


def test_writeonly_not_in_response():
    """Test that writeonly fields are not shown in list response"""

    class WriteonlyTestSerializer(serializers.ModelSerializer):
        '''Serializer for testing the absence of write_only fields'''
        comments = serializers.ResourceRelatedField(
            many=True,
            write_only=True,
            queryset=Comment.objects.all()
        )

        rating = serializers.IntegerField(write_only=True)

        class Meta:
            model = Entry
            fields = ('comments', 'rating')

    class WriteOnlyDummyTestViewSet(views.ReadOnlyModelViewSet):
        queryset = Entry.objects.all()
        serializer_class = WriteonlyTestSerializer

    rendered = render_dummy_test_serialized_view(WriteOnlyDummyTestViewSet, Entry())
    result = json.loads(rendered.decode())

    assert 'rating' not in result['data']['attributes']
    assert 'relationships' not in result['data']


def test_render_empty_relationship_reverse_lookup():
    """Test that empty relationships are rendered as None."""

    class EmptyRelationshipSerializer(serializers.ModelSerializer):
        class Meta:
            model = Author
            fields = ('bio', )

    class EmptyRelationshipViewSet(views.ReadOnlyModelViewSet):
        queryset = Author.objects.all()
        serializer_class = EmptyRelationshipSerializer

    rendered = render_dummy_test_serialized_view(EmptyRelationshipViewSet, Author())
    result = json.loads(rendered.decode())
    assert 'relationships' in result['data']
    assert 'bio' in result['data']['relationships']
    assert result['data']['relationships']['bio'] == {'data': None}


@pytest.mark.django_db
def test_extract_relation_instance(comment):
    serializer = RelatedModelSerializer(instance=comment)

    got = JSONRenderer.extract_relation_instance(
        field=serializer.fields['blog'], resource_instance=comment
    )
    assert got == comment.entry.blog
