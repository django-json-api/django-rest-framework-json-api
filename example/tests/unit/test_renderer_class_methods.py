import pytest
from django.contrib.auth import get_user_model

from drf_search_categories import serializers
from drf_search_categories.renderers import JSONRenderer

pytestmark = pytest.mark.django_db

class ResourceSerializer(serializers.ModelSerializer):
    version = serializers.SerializerMethodField()
    def get_version(self, obj):
        return '1.0.0'
    class Meta:
        fields = ('username',)
        meta_fields = ('version',)
        model = get_user_model()


def test_build_json_resource_obj():
    resource = {
        'pk': 1,
        'username': 'Alice',
    }

    serializer = ResourceSerializer(data={'username': 'Alice'})
    serializer.is_valid()
    resource_instance = serializer.save()

    output = {
        'type': 'user',
        'id': '1',
        'attributes': {
            'username': 'Alice'
        },
    }

    assert JSONRenderer.build_json_resource_obj(
        serializer.fields, resource, resource_instance, 'user') == output


def test_extract_attributes():
    fields = {
        'id': serializers.Field(),
        'username': serializers.Field(),
        'deleted': serializers.ReadOnlyField(),
    }
    resource = {'id': 1, 'deleted': None, 'username': 'jerel'}
    expected = {
        'username': 'jerel',
        'deleted': None
    }
    assert sorted(JSONRenderer.extract_attributes(fields, resource)) == sorted(expected), 'Regular fields should be extracted'
    assert sorted(JSONRenderer.extract_attributes(fields, {})) == sorted(
        {'username': ''}), 'Should not extract read_only fields on empty serializer'

def test_extract_meta():
    serializer = ResourceSerializer(data={'username': 'jerel', 'version':'1.0.0'})
    serializer.is_valid()
    expected = {
        'version': '1.0.0',
    }
    assert JSONRenderer.extract_meta(serializer, serializer.data) == expected

def test_extract_root_meta():
    def get_root_meta(obj):
        return {
            'foo': 'meta-value'
        }

    serializer = ResourceSerializer()
    serializer.get_root_meta = get_root_meta
    expected = {
        'foo': 'meta-value',
    }
    assert JSONRenderer.extract_root_meta(serializer, {}, {}) == expected

def test_extract_root_meta_many():
    def get_root_meta(obj):
        return {
          'foo': 'meta-value'
        }

    serializer = ResourceSerializer(many=True)
    serializer.get_root_meta = get_root_meta
    expected = {
      'foo': 'meta-value'
    }
    assert JSONRenderer.extract_root_meta(serializer, {}, {}) == expected

def test_extract_root_meta_invalid_meta():
    def get_root_meta(obj):
        return 'not a dict'

    serializer = ResourceSerializer()
    serializer.get_root_meta = get_root_meta
    with pytest.raises(AssertionError) as e_info:
        JSONRenderer.extract_root_meta(serializer, {}, {})

