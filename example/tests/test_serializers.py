import pytest
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import timezone

from rest_framework_json_api.serializers import ResourceIdentifierObjectSerializer
from rest_framework_json_api.utils import format_resource_type

from example.models import Author, Blog, Entry
from example.tests.utils import load_json

pytestmark = pytest.mark.django_db


class TestResourceIdentifierObjectSerializer(TestCase):
    def setUp(self):
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

        parsed_content = load_json(response.content)

        assert expected == parsed_content
