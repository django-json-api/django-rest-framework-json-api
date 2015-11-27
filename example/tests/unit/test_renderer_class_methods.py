from django.contrib.auth import get_user_model

from rest_framework_json_api import serializers
from rest_framework_json_api.renderers import JSONRenderer

pytestmark = pytest.mark.django_db

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('username',)
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
