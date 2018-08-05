from __future__ import absolute_import

from django.test.client import RequestFactory
from django.utils import timezone
from rest_framework import serializers
from rest_framework.fields import SkipField
from rest_framework.reverse import reverse

from rest_framework_json_api.exceptions import Conflict
from rest_framework_json_api.relations import (
    HyperlinkedRelatedField,
    ResourceRelatedField,
    SerializerMethodHyperlinkedRelatedField
)
from rest_framework_json_api.utils import format_resource_type

from . import TestBase
from example.models import Author, Blog, Comment, Entry
from example.serializers import CommentSerializer
from example.views import EntryViewSet


class TestResourceRelatedField(TestBase):

    def setUp(self):
        super(TestResourceRelatedField, self).setUp()
        self.blog = Blog.objects.create(name='Some Blog', tagline="It's a blog")
        self.entry = Entry.objects.create(
            blog=self.blog,
            headline='headline',
            body_text='body_text',
            pub_date=timezone.now(),
            mod_date=timezone.now(),
            n_comments=0,
            n_pingbacks=0,
            rating=3
        )
        for i in range(1, 6):
            name = 'some_author{}'.format(i)
            self.entry.authors.add(
                Author.objects.create(name=name, email='{}@example.org'.format(name))
            )

        self.comment = Comment.objects.create(
            entry=self.entry,
            body='testing one two three',
            author=Author.objects.first()
        )

    def test_data_in_correct_format_when_instantiated_with_blog_object(self):
        serializer = BlogFKSerializer(instance={'blog': self.blog})

        expected_data = {
            'type': format_resource_type('Blog'),
            'id': str(self.blog.id)
        }

        actual_data = serializer.data['blog']

        self.assertEqual(actual_data, expected_data)

    def test_data_in_correct_format_when_instantiated_with_entry_object(self):
        serializer = EntryFKSerializer(instance={'entry': self.entry})

        expected_data = {
            'type': format_resource_type('Entry'),
            'id': str(self.entry.id)
        }

        actual_data = serializer.data['entry']

        self.assertEqual(actual_data, expected_data)

    def test_deserialize_primitive_data_blog(self):
        serializer = BlogFKSerializer(data={
            'blog': {
                'type': format_resource_type('Blog'),
                'id': str(self.blog.id)
            }
        }
        )

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['blog'], self.blog)

    def test_validation_fails_for_wrong_type(self):
        with self.assertRaises(Conflict) as cm:
            serializer = BlogFKSerializer(data={
                'blog': {
                    'type': 'Entries',
                    'id': str(self.blog.id)
                }
            }
            )
            serializer.is_valid()
        the_exception = cm.exception
        self.assertEqual(the_exception.status_code, 409)

    def test_serialize_many_to_many_relation(self):
        serializer = EntryModelSerializer(instance=self.entry)

        type_string = format_resource_type('Author')
        author_pks = Author.objects.values_list('pk', flat=True)
        expected_data = [{'type': type_string, 'id': str(pk)} for pk in author_pks]

        self.assertEqual(
            serializer.data['authors'],
            expected_data
        )

    def test_deserialize_many_to_many_relation(self):
        type_string = format_resource_type('Author')
        author_pks = Author.objects.values_list('pk', flat=True)
        authors = [{'type': type_string, 'id': pk} for pk in author_pks]

        serializer = EntryModelSerializer(data={'authors': authors, 'comments': []})

        self.assertTrue(serializer.is_valid())
        self.assertEqual(len(serializer.validated_data['authors']), Author.objects.count())
        for author in serializer.validated_data['authors']:
            self.assertIsInstance(author, Author)

    def test_read_only(self):
        serializer = EntryModelSerializer(
            data={'authors': [], 'comments': [{'type': 'Comments', 'id': 2}]}
        )
        serializer.is_valid(raise_exception=True)
        self.assertNotIn('comments', serializer.validated_data)

    def test_invalid_resource_id_object(self):
        comment = {'body': 'testing 123', 'entry': {'type': 'entry'}, 'author': {'id': '5'}}
        serializer = CommentSerializer(data=comment)
        assert not serializer.is_valid()
        assert serializer.errors == {
            'author': ["Invalid resource identifier object: missing 'type' attribute"],
            'entry': ["Invalid resource identifier object: missing 'id' attribute"]
        }


class TestHyperlinkedFieldBase(TestBase):

    def setUp(self):
        super(TestHyperlinkedFieldBase, self).setUp()
        self.blog = Blog.objects.create(name='Some Blog', tagline="It's a blog")
        self.entry = Entry.objects.create(
            blog=self.blog,
            headline='headline',
            body_text='body_text',
            pub_date=timezone.now(),
            mod_date=timezone.now(),
            n_comments=0,
            n_pingbacks=0,
            rating=3
        )
        self.comment = Comment.objects.create(
            entry=self.entry,
            body='testing one two three',
        )

        self.request = RequestFactory().get(reverse('entry-detail', kwargs={'pk': self.entry.pk}))
        self.view = EntryViewSet(request=self.request, kwargs={'entry_pk': self.entry.id})


class TestHyperlinkedRelatedField(TestHyperlinkedFieldBase):

    def test_single_hyperlinked_related_field(self):
        field = HyperlinkedRelatedField(
            related_link_view_name='entry-blog',
            related_link_url_kwarg='entry_pk',
            self_link_view_name='entry-relationships',
            read_only=True,
        )
        field._context = {'request': self.request, 'view': self.view}
        field.field_name = 'blog'

        self.assertRaises(NotImplementedError, field.to_representation, self.entry)
        self.assertRaises(SkipField, field.get_attribute, self.entry)

        links_expected = {
            'self': 'http://testserver/entries/{}/relationships/blog'.format(self.entry.pk),
            'related': 'http://testserver/entries/{}/blog'.format(self.entry.pk)
        }
        got = field.get_links(self.entry)
        self.assertEqual(got, links_expected)

    def test_many_hyperlinked_related_field(self):
        field = HyperlinkedRelatedField(
            related_link_view_name='entry-comments',
            related_link_url_kwarg='entry_pk',
            self_link_view_name='entry-relationships',
            read_only=True,
            many=True
        )
        field._context = {'request': self.request, 'view': self.view}
        field.field_name = 'comments'

        self.assertRaises(NotImplementedError, field.to_representation, self.entry.comments.all())
        self.assertRaises(SkipField, field.get_attribute, self.entry)

        links_expected = {
            'self': 'http://testserver/entries/{}/relationships/comments'.format(self.entry.pk),
            'related': 'http://testserver/entries/{}/comments'.format(self.entry.pk)
        }
        got = field.child_relation.get_links(self.entry)
        self.assertEqual(got, links_expected)


class TestSerializerMethodHyperlinkedRelatedField(TestHyperlinkedFieldBase):

    def test_single_serializer_method_hyperlinked_related_field(self):
        serializer = EntryModelSerializerWithHyperLinks(
            instance=self.entry,
            context={
                'request': self.request,
                'view': self.view
            }
        )
        field = serializer.fields['blog']

        self.assertRaises(NotImplementedError, field.to_representation, self.entry)
        self.assertRaises(SkipField, field.get_attribute, self.entry)

        expected = {
            'self': 'http://testserver/entries/{}/relationships/blog'.format(self.entry.pk),
            'related': 'http://testserver/entries/{}/blog'.format(self.entry.pk)
        }
        got = field.get_links(self.entry)
        self.assertEqual(got, expected)

    def test_many_serializer_method_hyperlinked_related_field(self):
        serializer = EntryModelSerializerWithHyperLinks(
            instance=self.entry,
            context={
                'request': self.request,
                'view': self.view
            }
        )
        field = serializer.fields['comments']

        self.assertRaises(NotImplementedError, field.to_representation, self.entry)
        self.assertRaises(SkipField, field.get_attribute, self.entry)

        expected = {
            'self': 'http://testserver/entries/{}/relationships/comments'.format(self.entry.pk),
            'related': 'http://testserver/entries/{}/comments'.format(self.entry.pk)
        }
        got = field.get_links(self.entry)
        self.assertEqual(got, expected)

    def test_get_blog(self):
        serializer = EntryModelSerializerWithHyperLinks(instance=self.entry)
        got = serializer.get_blog(self.entry)
        expected = self.entry.blog

        self.assertEqual(got, expected)

    def test_get_comments(self):
        serializer = EntryModelSerializerWithHyperLinks(instance=self.entry)
        got = serializer.get_comments(self.entry)
        expected = self.entry.comments.all()

        self.assertListEqual(list(got), list(expected))


class BlogResourceRelatedField(ResourceRelatedField):
    def get_queryset(self):
        return Blog.objects


class BlogFKSerializer(serializers.Serializer):
    blog = BlogResourceRelatedField()


class EntryFKSerializer(serializers.Serializer):
    entry = ResourceRelatedField(queryset=Entry.objects)


class EntryModelSerializer(serializers.ModelSerializer):
    authors = ResourceRelatedField(many=True, queryset=Author.objects)
    comments = ResourceRelatedField(many=True, read_only=True)

    class Meta:
        model = Entry
        fields = ('authors', 'comments')


class EntryModelSerializerWithHyperLinks(serializers.ModelSerializer):
    blog = SerializerMethodHyperlinkedRelatedField(
        related_link_view_name='entry-blog',
        related_link_url_kwarg='entry_pk',
        self_link_view_name='entry-relationships',
        many=True,
        read_only=True,
        source='get_blog'
    )
    comments = SerializerMethodHyperlinkedRelatedField(
        related_link_view_name='entry-comments',
        related_link_url_kwarg='entry_pk',
        self_link_view_name='entry-relationships',
        many=True,
        read_only=True,
        source='get_comments'
    )

    class Meta:
        model = Entry
        fields = ('blog', 'comments',)

    def get_blog(self, obj):
        return obj.blog

    def get_comments(self, obj):
        return obj.comments.all()
