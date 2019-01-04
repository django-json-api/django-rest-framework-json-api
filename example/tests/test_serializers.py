import pytest
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from rest_framework_json_api.serializers import (
    DateField,
    ModelSerializer,
    ResourceIdentifierObjectSerializer
)
from rest_framework_json_api.utils import format_resource_type

from example.models import Author, Blog, Entry
from example.serializers import BlogSerializer

try:
    from unittest import mock
except ImportError:  # pragma: no cover
    import mock

request_factory = APIRequestFactory()
pytestmark = pytest.mark.django_db


class TestResourceIdentifierObjectSerializer(TestCase):
    def setUp(self):
        self.blog = Blog.objects.create(name='Some Blog', tagline="It's a blog")
        now = timezone.now()

        self.entry = Entry.objects.create(
            blog=self.blog,
            headline='headline',
            body_text='body_text',
            pub_date=now.date(),
            mod_date=now.date(),
            n_comments=0,
            n_pingbacks=0,
            rating=3
        )
        for i in range(1, 6):
            name = 'some_author{}'.format(i)
            self.entry.authors.add(
                Author.objects.create(name=name, email='{}@example.org'.format(name))
            )

    def test_forward_relationship_not_loaded_when_not_included(self):
        to_representation_method = 'example.serializers.BlogSerializer.to_representation'
        with mock.patch(to_representation_method) as mocked_serializer:
            class EntrySerializer(ModelSerializer):
                blog = BlogSerializer()

                class Meta:
                    model = Entry
                    fields = '__all__'

            request_without_includes = Request(request_factory.get('/'))
            serializer = EntrySerializer(context={'request': request_without_includes})
            serializer.to_representation(self.entry)

            mocked_serializer.assert_not_called()

    def test_forward_relationship_optimization_correct_representation(self):
        class EntrySerializer(ModelSerializer):
            blog = BlogSerializer()

            class Meta:
                model = Entry
                fields = '__all__'

        request_without_includes = Request(request_factory.get('/'))
        serializer = EntrySerializer(context={'request': request_without_includes})
        result = serializer.to_representation(self.entry)

        # Remove non deterministic fields
        result.pop('created_at')
        result.pop('modified_at')

        expected = dict(
            [
                ('id', 1),
                ('blog', dict([('type', 'blogs'), ('id', 1)])),
                ('headline', 'headline'),
                ('body_text', 'body_text'),
                ('pub_date', DateField().to_representation(self.entry.pub_date)),
                ('mod_date', DateField().to_representation(self.entry.mod_date)),
                ('n_comments', 0),
                ('n_pingbacks', 0),
                ('rating', 3),
                ('authors',
                    [
                        dict([('type', 'authors'), ('id', '1')]),
                        dict([('type', 'authors'), ('id', '2')]),
                        dict([('type', 'authors'), ('id', '3')]),
                        dict([('type', 'authors'), ('id', '4')]),
                        dict([('type', 'authors'), ('id', '5')])])])

        self.assertDictEqual(expected, result)

    def test_data_in_correct_format_when_instantiated_with_blog_object(self):
        serializer = ResourceIdentifierObjectSerializer(instance=self.blog)

        expected_data = {'type': format_resource_type('Blog'), 'id': str(self.blog.id)}

        assert serializer.data == expected_data

    def test_data_in_correct_format_when_instantiated_with_entry_object(self):
        serializer = ResourceIdentifierObjectSerializer(instance=self.entry)

        expected_data = {'type': format_resource_type('Entry'), 'id': str(self.entry.id)}

        assert serializer.data == expected_data

    def test_deserialize_primitive_data_blog(self):
        initial_data = {
            'type': format_resource_type('Blog'),
            'id': str(self.blog.id)
        }
        serializer = ResourceIdentifierObjectSerializer(data=initial_data, model_class=Blog)

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        assert serializer.validated_data == self.blog

    def test_data_in_correct_format_when_instantiated_with_queryset(self):
        qs = Author.objects.all()
        serializer = ResourceIdentifierObjectSerializer(instance=qs, many=True)

        type_string = format_resource_type('Author')
        author_pks = Author.objects.values_list('pk', flat=True)
        expected_data = [{'type': type_string, 'id': str(pk)} for pk in author_pks]

        assert serializer.data == expected_data

    def test_deserialize_many(self):
        type_string = format_resource_type('Author')
        author_pks = Author.objects.values_list('pk', flat=True)
        initial_data = [{'type': type_string, 'id': str(pk)} for pk in author_pks]

        serializer = ResourceIdentifierObjectSerializer(
            data=initial_data, model_class=Author, many=True
        )

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

        print(serializer.data)


class TestModelSerializer(object):
    def test_model_serializer_with_implicit_fields(self, comment, client):
        expected = {
            "data": {
                "type": "comments",
                "id": str(comment.pk),
                "attributes": {
                    "body": comment.body
                },
                "relationships": {
                    "entry": {
                        "data": {
                            "type": "entries",
                            "id": str(comment.entry.pk)
                        }
                    },
                    "author": {
                        "data": {
                            "type": "authors",
                            "id": str(comment.author.pk)
                        }
                    },
                    "writer": {
                        "data": {
                            "type": "writers",
                            "id": str(comment.author.pk)
                        }
                    },
                }
            }
        }

        response = client.get(reverse("comment-detail", kwargs={'pk': comment.pk}))

        assert response.status_code == 200
        assert expected == response.json()
