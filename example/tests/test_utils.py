import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_json_api import utils

pytestmark = pytest.mark.django_db

class ResourceView(APIView):
    pass

class ResourceSerializer(serializers.ModelSerializer):
    class Meta():
        fields = ('username',)
        model = get_user_model()

def test_get_resource_name():
    view = ResourceView()
    context = {'view': view}
    setattr(settings, 'JSON_API_FORMAT_RELATION_KEYS', None)
    assert 'ResourceViews' == utils.get_resource_name(context), 'not formatted'

    view = ResourceView()
    context = {'view': view}
    setattr(settings, 'JSON_API_FORMAT_RELATION_KEYS', 'dasherize')
    assert 'resource-views' == utils.get_resource_name(context), 'derived from view'

    view.model = get_user_model()
    assert 'users' == utils.get_resource_name(context), 'derived from view model'

    view.resource_name = 'custom'
    assert 'custom' == utils.get_resource_name(context), 'manually set on view'

    view.response = Response(status=403)
    assert 'errors' == utils.get_resource_name(context), 'handles 4xx error'

    view.response = Response(status=500)
    assert 'errors' == utils.get_resource_name(context), 'handles 500 error'

    view = ResourceView()
    context = {'view': view}
    view.serializer_class = ResourceSerializer
    assert 'users' == utils.get_resource_name(context), 'derived from serializer'

    view.serializer_class.Meta.resource_name = 'rcustom'
    assert 'rcustom' == utils.get_resource_name(context), 'set on serializer'

def test_format_keys():
    underscored = {
        'first_name': 'a',
        'last_name': 'b',
    }

    output = {'firstName': 'a', 'lastName': 'b'}
    assert utils.format_keys(underscored, 'camelize') == output

    output = {'FirstName': 'a', 'LastName': 'b'}
    assert utils.format_keys(underscored, 'capitalize') == output

    output = {'first-name': 'a', 'last-name': 'b'}
    assert utils.format_keys(underscored, 'dasherize') == output

    new_input = {'firstName': 'a', 'lastName': 'b'}
    assert utils.format_keys(new_input, 'underscore') == underscored

    output = [{'first-name': 'a', 'last-name': 'b'}]
    assert utils.format_keys([underscored], 'dasherize') == output

def test_format_value():
    assert utils.format_value('first_name', 'camelize') == 'firstName'
    assert utils.format_value('first_name', 'capitalize') == 'FirstName'
    assert utils.format_value('first_name', 'dasherize') == 'first-name'
    assert utils.format_value('first-name', 'underscore') == 'first_name'

def test_format_relation_name():
    assert utils.format_relation_name('first_name', 'capitalize') == 'FirstNames'
    assert utils.format_relation_name('first_name', 'camelize') == 'firstNames'

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

    assert utils.build_json_resource_obj(
            serializer.fields, resource, resource_instance, 'user') == output

