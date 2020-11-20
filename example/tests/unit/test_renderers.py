import json

import pytest
from django.utils import timezone

from rest_framework_json_api import serializers, views
from rest_framework_json_api.renderers import JSONRenderer

from example.models import Author, Blog, Comment, Entry


# serializers
class RelatedModelSerializer(serializers.ModelSerializer):
    blog = serializers.ReadOnlyField(source="entry.blog")

    class Meta:
        model = Comment
        fields = ("id", "blog")


class DummyTestSerializer(serializers.ModelSerializer):
    """
    This serializer is a simple compound document serializer which includes only
    a single embedded relation
    """

    related_models = RelatedModelSerializer(
        source="comments", many=True, read_only=True
    )

    json_field = serializers.SerializerMethodField()

    def get_json_field(self, entry):
        return {"JsonKey": "JsonValue"}

    class Meta:
        model = Entry
        fields = ("related_models", "json_field")

    class JSONAPIMeta:
        included_resources = ("related_models",)


class EntryDRFSerializers(serializers.ModelSerializer):
    class Meta:
        model = Entry
        fields = ("headline", "body_text")
        read_only_fields = ("tags",)


class CommentWithNestedFieldsSerializer(serializers.ModelSerializer):
    entry = EntryDRFSerializers()

    class Meta:
        model = Comment
        exclude = ("created_at", "modified_at", "author")
        # fields = ('entry', 'body', 'author',)


class AuthorWithNestedFieldsSerializer(serializers.ModelSerializer):
    comments = CommentWithNestedFieldsSerializer(many=True)

    class Meta:
        model = Author
        fields = ("name", "email", "comments")


# views
class DummyTestViewSet(views.ModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = DummyTestSerializer


class ReadOnlyDummyTestViewSet(views.ReadOnlyModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = DummyTestSerializer


class AuthorWithNestedFieldsViewSet(views.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorWithNestedFieldsSerializer
    resource_name = "authors"


def render_dummy_test_serialized_view(view_class, instance):
    serializer = view_class.serializer_class(instance=instance)
    renderer = JSONRenderer()
    return renderer.render(serializer.data, renderer_context={"view": view_class()})


def test_simple_reverse_relation_included_renderer():
    """
    Test renderer when a single reverse fk relation is passed.
    """
    rendered = render_dummy_test_serialized_view(DummyTestViewSet, Entry())

    assert rendered


def test_simple_reverse_relation_included_read_only_viewset():
    rendered = render_dummy_test_serialized_view(ReadOnlyDummyTestViewSet, Entry())

    assert rendered


def test_render_format_field_names(settings):
    """Test that json field is kept untouched."""
    settings.JSON_API_FORMAT_FIELD_NAMES = "dasherize"
    rendered = render_dummy_test_serialized_view(DummyTestViewSet, Entry())

    result = json.loads(rendered.decode())
    assert result["data"]["attributes"]["json-field"] == {"JsonKey": "JsonValue"}


def test_writeonly_not_in_response():
    """Test that writeonly fields are not shown in list response"""

    class WriteonlyTestSerializer(serializers.ModelSerializer):
        """Serializer for testing the absence of write_only fields"""

        comments = serializers.ResourceRelatedField(
            many=True, write_only=True, queryset=Comment.objects.all()
        )

        rating = serializers.IntegerField(write_only=True)

        class Meta:
            model = Entry
            fields = ("comments", "rating")

    class WriteOnlyDummyTestViewSet(views.ReadOnlyModelViewSet):
        queryset = Entry.objects.all()
        serializer_class = WriteonlyTestSerializer

    rendered = render_dummy_test_serialized_view(WriteOnlyDummyTestViewSet, Entry())
    result = json.loads(rendered.decode())

    assert "rating" not in result["data"]["attributes"]
    assert "relationships" not in result["data"]


def test_render_empty_relationship_reverse_lookup():
    """Test that empty relationships are rendered as None."""

    class EmptyRelationshipSerializer(serializers.ModelSerializer):
        class Meta:
            model = Author
            fields = ("bio",)

    class EmptyRelationshipViewSet(views.ReadOnlyModelViewSet):
        queryset = Author.objects.all()
        serializer_class = EmptyRelationshipSerializer

    rendered = render_dummy_test_serialized_view(EmptyRelationshipViewSet, Author())
    result = json.loads(rendered.decode())
    assert "relationships" in result["data"]
    assert "bio" in result["data"]["relationships"]
    assert result["data"]["relationships"]["bio"] == {"data": None}


@pytest.mark.django_db
def test_extract_relation_instance(comment):
    serializer = RelatedModelSerializer(instance=comment)

    got = JSONRenderer.extract_relation_instance(
        field=serializer.fields["blog"], resource_instance=comment
    )
    assert got == comment.entry.blog


def test_render_serializer_as_attribute(db):
    # setting up
    blog = Blog.objects.create(name="Some Blog", tagline="It's a blog")
    entry = Entry.objects.create(
        blog=blog,
        headline="headline",
        body_text="body_text",
        pub_date=timezone.now(),
        mod_date=timezone.now(),
        n_comments=0,
        n_pingbacks=0,
        rating=3,
    )

    author = Author.objects.create(name="some_author", email="some_author@example.org")
    entry.authors.add(author)

    Comment.objects.create(
        entry=entry, body="testing one two three", author=Author.objects.first()
    )

    rendered = render_dummy_test_serialized_view(AuthorWithNestedFieldsViewSet, author)
    result = json.loads(rendered.decode())

    expected = {
        "data": {
            "type": "authors",
            "id": "1",
            "attributes": {
                "name": "some_author",
                "email": "some_author@example.org",
                "comments": [
                    {
                        "id": 1,
                        "entry": {
                            "headline": "headline",
                            "body_text": "body_text",
                        },
                        "body": "testing one two three",
                    }
                ],
            },
        }
    }
    assert expected == result
