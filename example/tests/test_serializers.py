from datetime import datetime
from unittest import mock

import pytest
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from rest_framework_json_api.serializers import (
    DateField,
    ModelSerializer,
    ResourceIdentifierObjectSerializer,
    empty,
)
from rest_framework_json_api.utils import format_resource_type

from example.factories import ArtProjectFactory
from example.models import Author, Blog, Entry
from example.serializers import ArtProjectSerializer, BlogSerializer, ProjectSerializer

request_factory = APIRequestFactory()
pytestmark = pytest.mark.django_db


class TestResourceIdentifierObjectSerializer(TestCase):
    def setUp(self):
        self.blog = Blog.objects.create(name="Some Blog", tagline="It's a blog")
        now = timezone.now()

        self.entry = Entry.objects.create(
            blog=self.blog,
            headline="headline",
            body_text="body_text",
            pub_date=now.date(),
            mod_date=now.date(),
            n_comments=0,
            n_pingbacks=0,
            rating=3,
        )
        for i in range(1, 6):
            name = f"some_author{i}"
            self.entry.authors.add(
                Author.objects.create(name=name, email=f"{name}@example.org")
            )

    def test_forward_relationship_not_loaded_when_not_included(self):
        to_representation_method = (
            "example.serializers.TaggedItemSerializer.to_representation"
        )
        with mock.patch(to_representation_method) as mocked_serializer:

            class EntrySerializer(ModelSerializer):
                blog = BlogSerializer()

                class Meta:
                    model = Entry
                    fields = "__all__"

            request_without_includes = Request(request_factory.get("/"))
            serializer = EntrySerializer(context={"request": request_without_includes})
            serializer.to_representation(self.entry)

            mocked_serializer.assert_not_called()

    def test_forward_relationship_optimization_correct_representation(self):
        class EntrySerializer(ModelSerializer):
            blog = BlogSerializer()

            class Meta:
                model = Entry
                fields = "__all__"

        request_without_includes = Request(request_factory.get("/"))
        serializer = EntrySerializer(context={"request": request_without_includes})
        result = serializer.to_representation(self.entry)

        # Remove non deterministic fields
        result.pop("created_at")
        result.pop("modified_at")

        expected = dict(
            [
                ("id", 1),
                (
                    "blog",
                    dict(
                        [
                            ("name", "Some Blog"),
                            ("tags", []),
                            ("copyright", datetime.now().year),
                            ("url", "http://testserver/blogs/1"),
                        ]
                    ),
                ),
                ("headline", "headline"),
                ("body_text", "body_text"),
                ("pub_date", DateField().to_representation(self.entry.pub_date)),
                ("mod_date", DateField().to_representation(self.entry.mod_date)),
                ("n_comments", 0),
                ("n_pingbacks", 0),
                ("rating", 3),
                (
                    "authors",
                    [
                        dict([("type", "authors"), ("id", "1")]),
                        dict([("type", "authors"), ("id", "2")]),
                        dict([("type", "authors"), ("id", "3")]),
                        dict([("type", "authors"), ("id", "4")]),
                        dict([("type", "authors"), ("id", "5")]),
                    ],
                ),
            ]
        )

        self.assertDictEqual(expected, result)

    def test_data_in_correct_format_when_instantiated_with_blog_object(self):
        serializer = ResourceIdentifierObjectSerializer(instance=self.blog)

        expected_data = {"type": format_resource_type("Blog"), "id": str(self.blog.id)}

        assert serializer.data == expected_data

    def test_data_in_correct_format_when_instantiated_with_entry_object(self):
        serializer = ResourceIdentifierObjectSerializer(instance=self.entry)

        expected_data = {
            "type": format_resource_type("Entry"),
            "id": str(self.entry.id),
        }

        assert serializer.data == expected_data

    def test_deserialize_primitive_data_blog(self):
        initial_data = {"type": format_resource_type("Blog"), "id": str(self.blog.id)}
        serializer = ResourceIdentifierObjectSerializer(
            data=initial_data, model_class=Blog
        )

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        assert serializer.validated_data == self.blog

    def test_deserialize_primitive_data_blog_with_unexisting_pk(self):
        unexisting_pk = self.blog.id
        self.blog.delete()
        assert not Blog.objects.filter(id=unexisting_pk).exists()

        initial_data = {"type": format_resource_type("Blog"), "id": str(unexisting_pk)}
        serializer = ResourceIdentifierObjectSerializer(
            data=initial_data, model_class=Blog
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors[0].code, "does_not_exist")

    def test_data_in_correct_format_when_instantiated_with_queryset(self):
        qs = Author.objects.all()
        serializer = ResourceIdentifierObjectSerializer(instance=qs, many=True)

        type_string = format_resource_type("Author")
        author_pks = Author.objects.values_list("pk", flat=True)
        expected_data = [{"type": type_string, "id": str(pk)} for pk in author_pks]

        assert serializer.data == expected_data

    def test_deserialize_many(self):
        type_string = format_resource_type("Author")
        author_pks = Author.objects.values_list("pk", flat=True)
        initial_data = [{"type": type_string, "id": str(pk)} for pk in author_pks]

        serializer = ResourceIdentifierObjectSerializer(
            data=initial_data, model_class=Author, many=True
        )

        self.assertTrue(serializer.is_valid(), msg=serializer.errors)

        print(serializer.data)


class TestModelSerializer:
    def test_model_serializer_with_implicit_fields(self, comment, client):
        expected = {
            "data": {
                "type": "comments",
                "id": str(comment.pk),
                "attributes": {"body": comment.body},
                "relationships": {
                    "entry": {"data": {"type": "entries", "id": str(comment.entry.pk)}},
                    "author": {
                        "data": {"type": "authors", "id": str(comment.author.pk)}
                    },
                    "writer": {
                        "data": {"type": "writers", "id": str(comment.author.pk)}
                    },
                },
                "meta": {
                    "modifiedDaysAgo": (datetime.now() - comment.modified_at).days
                },
            },
            "included": [
                {
                    "attributes": {
                        "email": comment.author.email,
                        "name": comment.author.name,
                    },
                    "id": str(comment.author.pk),
                    "relationships": {
                        "bio": {
                            "data": {
                                "id": str(comment.author.bio.pk),
                                "type": "authorBios",
                            }
                        }
                    },
                    "type": "writers",
                }
            ],
        }

        response = client.get(reverse("comment-detail", kwargs={"pk": comment.pk}))

        assert response.status_code == 200
        assert expected == response.json()


class TestPolymorphicModelSerializer(TestCase):
    def setUp(self):
        self.project = ArtProjectFactory.create()
        self.child_init_args = {}

        # Override `__init__` with our own method
        def overridden_init(child_self, instance=None, data=empty, **kwargs):
            """
            Override `ArtProjectSerializer.__init__` with the same signature that
            `BaseSerializer.__init__` has to assert that it receives the parameters
            that `BaseSerializer` expects
            """
            self.child_init_args = dict(instance=instance, data=data, **kwargs)

            return super(ArtProjectSerializer, child_self).__init__(
                instance, data, **kwargs
            )

        self.child_serializer_init = ArtProjectSerializer.__init__
        ArtProjectSerializer.__init__ = overridden_init

    def tearDown(self):
        # Restore original init to avoid affecting other tests
        ArtProjectSerializer.__init__ = self.child_serializer_init

    def test_polymorphic_model_serializer_passes_instance_to_child(self):
        """
        Ensure that `PolymorphicModelSerializer` is passing the instance to the
        child serializer when initializing them
        """
        # Initialize a serializer that would partially update a model instance
        initial_data = {"artist": "Mark Bishop", "type": "artProjects"}
        parent_serializer = ProjectSerializer(
            instance=self.project, data=initial_data, partial=True
        )

        parent_serializer.is_valid(raise_exception=True)

        # Run save to force `ProjectSerializer` to init `ArtProjectSerializer`
        parent_serializer.save()

        # Assert that child init received the expected arguments
        assert self.child_init_args["instance"] == self.project
        assert self.child_init_args["data"] == initial_data
        assert self.child_init_args["partial"] == parent_serializer.partial
        assert self.child_init_args["context"] == parent_serializer.context
