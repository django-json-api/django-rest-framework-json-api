from rest_framework_json_api import serializers, views
from rest_framework_json_api.renderers import JSONRenderer

from example.models import Comment, Entry


# serializers
class RelatedModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id',)


class DummyTestSerializer(serializers.ModelSerializer):
    '''
    This serializer is a simple compound document serializer which includes only
    a single embedded relation
    '''
    related_models = RelatedModelSerializer(
        source='comments', many=True, read_only=True)

    class Meta:
        model = Entry
        fields = ('related_models',)

    class JSONAPIMeta:
        included_resources = ('related_models',)


# views
class DummyTestViewSet(views.ModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = DummyTestSerializer


def test_simple_reverse_relation_included_renderer():
    '''
    Test renderer when a single reverse fk relation is passed.
    '''
    serializer = DummyTestSerializer(instance=Entry())
    renderer = JSONRenderer()
    rendered = renderer.render(
        serializer.data,
        renderer_context={'view': DummyTestViewSet()})

    assert rendered
