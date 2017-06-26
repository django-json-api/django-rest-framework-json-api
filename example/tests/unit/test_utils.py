import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import six
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_json_api import utils
from rest_framework_json_api.utils import get_included_serializers

from example.serializers import AuthorSerializer, BlogSerializer, CommentSerializer, EntrySerializer

pytestmark = pytest.mark.django_db


class NonModelResourceSerializer(serializers.Serializer):
    class Meta:
        resource_name = 'users'


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('username',)
        model = get_user_model()


def test_get_resource_name():
    view = APIView()
    context = {'view': view}
    setattr(settings, 'JSON_API_FORMAT_TYPES', None)
    assert 'APIViews' == utils.get_resource_name(context), 'not formatted'

    context = {'view': view}
    setattr(settings, 'JSON_API_FORMAT_TYPES', 'dasherize')
    assert 'api-views' == utils.get_resource_name(context), 'derived from view'

    view.model = get_user_model()
    assert 'users' == utils.get_resource_name(context), 'derived from view model'

    view.resource_name = 'custom'
    assert 'custom' == utils.get_resource_name(context), 'manually set on view'

    view.response = Response(status=403)
    assert 'errors' == utils.get_resource_name(context), 'handles 4xx error'

    view.response = Response(status=500)
    assert 'errors' == utils.get_resource_name(context), 'handles 500 error'

    view = GenericAPIView()
    view.serializer_class = ResourceSerializer
    context = {'view': view}
    assert 'users' == utils.get_resource_name(context), 'derived from serializer'

    view.serializer_class.Meta.resource_name = 'rcustom'
    assert 'rcustom' == utils.get_resource_name(context), 'set on serializer'

    view = GenericAPIView()
    view.serializer_class = NonModelResourceSerializer
    context = {'view': view}
    assert 'users' == utils.get_resource_name(context), 'derived from non-model serializer'


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


def test_format_resource_type():
    assert utils.format_resource_type('first_name', 'capitalize') == 'FirstNames'
    assert utils.format_resource_type('first_name', 'camelize') == 'firstNames'


class SerializerWithIncludedSerializers(EntrySerializer):
    included_serializers = {
        'blog': BlogSerializer,
        'authors': 'example.serializers.AuthorSerializer',
        'comments': 'example.serializers.CommentSerializer',
        'self': 'self'  # this wouldn't make sense in practice (and would be prohibited by
        # IncludedResourcesValidationMixin) but it's useful for the test
    }


def test_get_included_serializers_against_class():
    klass = SerializerWithIncludedSerializers
    included_serializers = get_included_serializers(klass)
    expected_included_serializers = {
        'blog': BlogSerializer,
        'authors': AuthorSerializer,
        'comments': CommentSerializer,
        'self': klass
    }
    assert six.viewkeys(included_serializers) == six.viewkeys(klass.included_serializers), (
        'the keys must be preserved'
    )

    assert included_serializers == expected_included_serializers


def test_get_included_serializers_against_instance():
    klass = SerializerWithIncludedSerializers
    instance = klass()
    included_serializers = get_included_serializers(instance)
    expected_included_serializers = {
        'blog': BlogSerializer,
        'authors': AuthorSerializer,
        'comments': CommentSerializer,
        'self': klass
    }
    assert six.viewkeys(included_serializers) == six.viewkeys(klass.included_serializers), (
        'the keys must be preserved'
    )

    assert included_serializers == expected_included_serializers
