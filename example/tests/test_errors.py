import pytest
from django.test import override_settings
from django.urls import path, reverse
from rest_framework import views

from rest_framework_json_api import serializers

from example.models import Blog


# serializers
class CommentAttachmentSerializer(serializers.Serializer):
    data = serializers.CharField(allow_null=False, required=True)

    def validate_data(self, value):
        if value and len(value) < 10:
            raise serializers.ValidationError("Too short data")


class CommentSerializer(serializers.Serializer):
    attachments = CommentAttachmentSerializer(many=True, required=False)
    attachment = CommentAttachmentSerializer(required=False)
    one_more_attachment = CommentAttachmentSerializer(required=False)
    body = serializers.CharField(allow_null=False, required=True)


class EntrySerializer(serializers.Serializer):
    blog = serializers.IntegerField()
    comments = CommentSerializer(many=True, required=False)
    comment = CommentSerializer(required=False)
    headline = serializers.CharField(allow_null=True, required=True)
    body_text = serializers.CharField()

    def validate(self, attrs):
        body_text = attrs["body_text"]
        if len(body_text) < 5:
            raise serializers.ValidationError(
                {"body_text": {"title": "Too Short title", "detail": "Too short"}}
            )


# view
class DummyTestView(views.APIView):
    serializer_class = EntrySerializer
    resource_name = "entries"

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)


urlpatterns = [
    path("entries-nested", DummyTestView.as_view(), name="entries-nested-list")
]


@pytest.fixture(scope="function")
def some_blog(db):
    return Blog.objects.create(name="Some Blog", tagline="It's a blog")


def perform_error_test(client, data):
    with override_settings(ROOT_URLCONF=__name__):
        url = reverse("entries-nested-list")
        response = client.post(url, data=data)

    return response.json()


def test_first_level_attribute_error(client, some_blog, snapshot):
    data = {
        "data": {
            "type": "entries",
            "attributes": {
                "blog": some_blog.pk,
                "bodyText": "body_text",
            },
        }
    }
    snapshot.assert_match(perform_error_test(client, data))


def test_first_level_custom_attribute_error(client, some_blog, snapshot):
    data = {
        "data": {
            "type": "entries",
            "attributes": {
                "blog": some_blog.pk,
                "body-text": "body",
                "headline": "headline",
            },
        }
    }
    with override_settings(JSON_API_FORMAT_FIELD_NAMES="dasherize"):
        snapshot.assert_match(perform_error_test(client, data))


def test_second_level_array_error(client, some_blog, snapshot):
    data = {
        "data": {
            "type": "entries",
            "attributes": {
                "blog": some_blog.pk,
                "bodyText": "body_text",
                "headline": "headline",
                "comments": [{}],
            },
        }
    }

    snapshot.assert_match(perform_error_test(client, data))


def test_second_level_dict_error(client, some_blog, snapshot):
    data = {
        "data": {
            "type": "entries",
            "attributes": {
                "blog": some_blog.pk,
                "bodyText": "body_text",
                "headline": "headline",
                "comment": {},
            },
        }
    }

    snapshot.assert_match(perform_error_test(client, data))


def test_third_level_array_error(client, some_blog, snapshot):
    data = {
        "data": {
            "type": "entries",
            "attributes": {
                "blog": some_blog.pk,
                "bodyText": "body_text",
                "headline": "headline",
                "comments": [{"body": "test comment", "attachments": [{}]}],
            },
        }
    }

    snapshot.assert_match(perform_error_test(client, data))


def test_third_level_custom_array_error(client, some_blog, snapshot):
    data = {
        "data": {
            "type": "entries",
            "attributes": {
                "blog": some_blog.pk,
                "bodyText": "body_text",
                "headline": "headline",
                "comments": [
                    {"body": "test comment", "attachments": [{"data": "text"}]}
                ],
            },
        }
    }

    snapshot.assert_match(perform_error_test(client, data))


def test_third_level_dict_error(client, some_blog, snapshot):
    data = {
        "data": {
            "type": "entries",
            "attributes": {
                "blog": some_blog.pk,
                "bodyText": "body_text",
                "headline": "headline",
                "comments": [{"body": "test comment", "attachment": {}}],
            },
        }
    }

    snapshot.assert_match(perform_error_test(client, data))


def test_many_third_level_dict_errors(client, some_blog, snapshot):
    data = {
        "data": {
            "type": "entries",
            "attributes": {
                "blog": some_blog.pk,
                "bodyText": "body_text",
                "headline": "headline",
                "comments": [{"attachment": {}}],
            },
        }
    }

    snapshot.assert_match(perform_error_test(client, data))
