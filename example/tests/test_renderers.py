from django.test import TestCase

from example.models import Blog, Entry, Comment
from example.serializers import EntrySerializer
from rest_framework_json_api import serializers
from rest_framework_json_api.renderers import JSONRenderer


class TestJSONRenderer(TestCase):

    def setUp(self):
        pass

    def test_extract_relation_instance(self):

        class NewEntySerializer(EntrySerializer):
            blog_name = serializers.ReadOnlyField(source='blog.name')

            class Meta(EntrySerializer.Meta):
                fields = EntrySerializer.Meta.fields + ('blog_name',)

        blog = Blog.objects.create(name='Some Blog', tagline="It's a blog")
        entry = Entry.objects.create(
            blog=blog,
            headline='headline',
            body_text='body_text',
        )
        suggested_enty = Entry.objects.create(
            blog=blog,
            headline='suggested headline',
            body_text='suggested body_text',
        )
        Comment.objects.create(entry=entry, body='foo')
        serializer = NewEntySerializer(instance=entry)

        got = JSONRenderer.extract_relation_instance(
            field=serializer.fields['featured'], resource_instance=entry
        )
        assert got == suggested_enty

        got = JSONRenderer.extract_relation_instance(
            field=serializer.fields['comments'], resource_instance=entry
        )
        assert str(got.query) == str(Comment.objects.filter(entry=entry).query)

        got = JSONRenderer.extract_relation_instance(
            field=serializer.fields['blog_name'], resource_instance=entry
        )
        assert got == blog.name
