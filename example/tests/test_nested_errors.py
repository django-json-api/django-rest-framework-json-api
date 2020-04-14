import pytest
from django.conf.urls import url
from django.test import override_settings
from django.urls import reverse

from example.models import Blog
from example.tests import TestBase
from rest_framework_json_api import serializers
from rest_framework import views


# serializers
class CommentAttachmentSerializer(serializers.Serializer):
    data = serializers.CharField(allow_null=False, required=True)

    def validate_data(self, value):
        if value and len(value) < 10:
            raise serializers.ValidationError('Too short data')


class CommentSerializer(serializers.Serializer):
    attachments = CommentAttachmentSerializer(many=True, required=False)
    attachment = CommentAttachmentSerializer(required=False)
    body = serializers.CharField(allow_null=False, required=True)


class EntrySerializer(serializers.Serializer):
    blog = serializers.IntegerField()
    comments = CommentSerializer(many=True, required=False)
    comment = CommentSerializer(required=False)
    headline = serializers.CharField(allow_null=True, required=True)
    body_text = serializers.CharField()

    def validate(self, attrs):
        body_text = attrs['body_text']
        if len(body_text) < 5:
            raise serializers.ValidationError({'body_text': 'Too short'})


# view
class DummyTestView(views.APIView):
    serializer_class = EntrySerializer
    resource_name = 'entries'

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)


urlpatterns = [
    url(r'^entries-nested/$', DummyTestView.as_view(),
        name='entries-nested-list')
]


@override_settings(ROOT_URLCONF=__name__)
class TestNestedErrors(TestBase):

    def setUp(self):
        super(TestNestedErrors, self).setUp()
        self.url = reverse('entries-nested-list')
        self.blog = Blog.objects.create(name='Some Blog', tagline="It's a blog")

    def perform_error_test(self, data, expected_pointer):
        with override_settings(
                JSON_API_SERIALIZE_NESTED_SERIALIZERS_AS_ATTRIBUTE=True):
            response = self.client.post(self.url, data=data)

        errors = response.data

        assert len(errors) == 1
        assert errors[0]['source']['pointer'] == expected_pointer

    def test_first_level_attribute_error(self):
        data = {
            'data': {
                'type': 'entries',
                'attributes': {
                    'blog': self.blog.pk,
                    'body_text': 'body_text',
                }
            }
        }
        self.perform_error_test(data, '/data/attributes/headline')

    def test_first_level_custom_attribute_error(self):
        data = {
            'data': {
                'type': 'entries',
                'attributes': {
                    'blog': self.blog.pk,
                    'body_text': 'body',
                    'headline': 'headline'
                }
            }
        }
        with override_settings(JSON_API_FORMAT_FIELD_NAMES='underscore'):
            self.perform_error_test(data, '/data/attributes/body_text')

    def test_second_level_array_error(self):
        data = {
            'data': {
                'type': 'entries',
                'attributes': {
                    'blog': self.blog.pk,
                    'body_text': 'body_text',
                    'headline': 'headline',
                    'comments': [
                        {
                        }
                    ]
                }
            }
        }

        self.perform_error_test(data, '/data/attributes/comments/0/body')

    def test_second_level_dict_error(self):
        data = {
            'data': {
                'type': 'entries',
                'attributes': {
                    'blog': self.blog.pk,
                    'body_text': 'body_text',
                    'headline': 'headline',
                    'comment': {}
                }
            }
        }

        self.perform_error_test(data, '/data/attributes/comment/body')

    def test_third_level_array_error(self):
        data = {
            'data': {
                'type': 'entries',
                'attributes': {
                    'blog': self.blog.pk,
                    'body_text': 'body_text',
                    'headline': 'headline',
                    'comments': [
                        {
                            'body': 'test comment',
                            'attachments': [
                                {
                                }
                            ]
                        }
                    ]
                }
            }
        }

        self.perform_error_test(data, '/data/attributes/comments/0/attachments/0/data')

    def test_third_level_custom_array_error(self):
        data = {
            'data': {
                'type': 'entries',
                'attributes': {
                    'blog': self.blog.pk,
                    'body_text': 'body_text',
                    'headline': 'headline',
                    'comments': [
                        {
                            'body': 'test comment',
                            'attachments': [
                                {
                                    'data': 'text'
                                }
                            ]
                        }
                    ]
                }
            }
        }

        self.perform_error_test(data, '/data/attributes/comments/0/attachments/0/data')

    def test_third_level_dict_error(self):
        data = {
            'data': {
                'type': 'entries',
                'attributes': {
                    'blog': self.blog.pk,
                    'body_text': 'body_text',
                    'headline': 'headline',
                    'comments': [
                        {
                            'body': 'test comment',
                            'attachment': {}
                        }
                    ]
                }
            }
        }

        self.perform_error_test(data, '/data/attributes/comments/0/attachment/data')


@pytest.mark.filterwarning('default::DeprecationWarning:rest_framework_json_api.serializers')
def test_deprecation_warning(recwarn):
    class DummyNestedSerializer(serializers.Serializer):
        field = serializers.CharField()

    class DummySerializer(serializers.Serializer):
        nested = DummyNestedSerializer(many=True)

    assert len(recwarn) == 1
    warning = recwarn.pop(DeprecationWarning)
    assert warning
    assert str(warning.message).startswith('Rendering')
