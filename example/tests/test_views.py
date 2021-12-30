import json
from datetime import datetime

from django.test import RequestFactory, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from rest_framework_json_api import serializers, views
from rest_framework_json_api.utils import format_resource_type

from example.factories import AuthorFactory, CommentFactory, EntryFactory
from example.models import Author, Blog, Comment, Entry
from example.serializers import (
    AuthorBioSerializer,
    AuthorTypeSerializer,
    EntrySerializer,
)
from example.tests import TestBase
from example.views import AuthorViewSet, BlogViewSet


class TestRelationshipView(APITestCase):
    def setUp(self):
        self.author = Author.objects.create(
            name="Super powerful superhero", email="i.am@lost.com"
        )
        self.blog = Blog.objects.create(name="Some Blog", tagline="It's a blog")
        self.other_blog = Blog.objects.create(
            name="Other blog", tagline="It's another blog"
        )
        self.first_entry = Entry.objects.create(
            blog=self.blog,
            headline="headline one",
            body_text="body_text two",
            pub_date=timezone.now(),
            mod_date=timezone.now(),
            n_comments=0,
            n_pingbacks=0,
            rating=3,
        )
        self.second_entry = Entry.objects.create(
            blog=self.blog,
            headline="headline two",
            body_text="body_text one",
            pub_date=timezone.now(),
            mod_date=timezone.now(),
            n_comments=0,
            n_pingbacks=0,
            rating=1,
        )
        self.first_comment = Comment.objects.create(
            entry=self.first_entry, body="This entry is cool", author=None
        )
        self.second_comment = Comment.objects.create(
            entry=self.second_entry, body="This entry is not cool", author=self.author
        )

    def test_get_entry_relationship_blog(self):
        url = reverse(
            "entry-relationships",
            kwargs={"pk": self.first_entry.id, "related_field": "blog"},
        )
        response = self.client.get(url)
        expected_data = {
            "type": format_resource_type("Blog"),
            "id": str(self.first_entry.blog.id),
        }

        assert response.data == expected_data

    def test_get_entry_relationship_invalid_field(self):
        response = self.client.get(
            f"/entries/{self.first_entry.id}/relationships/invalid_field"
        )

        assert response.status_code == 404

    def test_get_blog_relationship_entry_set(self):
        response = self.client.get(f"/blogs/{self.blog.id}/relationships/entry_set")
        expected_data = [
            {"type": format_resource_type("Entry"), "id": str(self.first_entry.id)},
            {"type": format_resource_type("Entry"), "id": str(self.second_entry.id)},
        ]

        assert response.data == expected_data

    @override_settings(JSON_API_FORMAT_RELATED_LINKS="dasherize")
    def test_get_blog_relationship_entry_set_with_formatted_link(self):
        response = self.client.get(f"/blogs/{self.blog.id}/relationships/entry-set")
        expected_data = [
            {"type": format_resource_type("Entry"), "id": str(self.first_entry.id)},
            {"type": format_resource_type("Entry"), "id": str(self.second_entry.id)},
        ]

        assert response.data == expected_data

    def test_put_entry_relationship_blog_returns_405(self):
        url = f"/entries/{self.first_entry.id}/relationships/blog"
        response = self.client.put(url, data={})
        assert response.status_code == 405

    def test_patch_invalid_entry_relationship_blog_returns_400(self):
        url = f"/entries/{self.first_entry.id}/relationships/blog"
        response = self.client.patch(url, data={"data": {"invalid": ""}})
        assert response.status_code == 400

    def test_relationship_view_errors_format(self):
        url = f"/entries/{self.first_entry.id}/relationships/blog"
        response = self.client.patch(url, data={"data": {"invalid": ""}})
        assert response.status_code == 400

        result = json.loads(response.content.decode("utf-8"))

        assert "data" not in result
        assert "errors" in result

    def test_get_empty_to_one_relationship(self):
        url = f"/comments/{self.first_entry.id}/relationships/author"
        response = self.client.get(url)
        expected_data = None

        assert response.data == expected_data

    def test_get_to_many_relationship_self_link(self):
        url = f"/authors/{self.author.id}/relationships/comments"

        response = self.client.get(url)
        expected_data = {
            "links": {"self": "http://testserver/authors/1/relationships/comments"},
            "data": [
                {
                    "id": str(self.second_comment.id),
                    "type": format_resource_type("Comment"),
                }
            ],
        }
        assert json.loads(response.content.decode("utf-8")) == expected_data

    def test_patch_to_one_relationship(self):
        url = f"/entries/{self.first_entry.id}/relationships/blog"
        request_data = {
            "data": {
                "type": format_resource_type("Blog"),
                "id": str(self.other_blog.id),
            }
        }
        response = self.client.patch(url, data=request_data)
        assert response.status_code == 200, response.content.decode()
        assert response.data == request_data["data"]

        response = self.client.get(url)
        assert response.data == request_data["data"]

    def test_patch_one_to_many_relationship(self):
        url = f"/blogs/{self.first_entry.id}/relationships/entry_set"
        request_data = {
            "data": [
                {"type": format_resource_type("Entry"), "id": str(self.first_entry.id)},
            ]
        }
        response = self.client.patch(url, data=request_data)
        assert response.status_code == 200, response.content.decode()
        assert response.data == request_data["data"]

        response = self.client.get(url)
        assert response.data == request_data["data"]

        # retry a second time should end up with same result
        response = self.client.patch(url, data=request_data)
        assert response.status_code == 200, response.content.decode()
        assert response.data == request_data["data"]

        response = self.client.get(url)
        assert response.data == request_data["data"]

    def test_patch_one_to_many_relaitonship_with_none(self):
        url = f"/blogs/{self.first_entry.id}/relationships/entry_set"
        request_data = {"data": None}
        response = self.client.patch(url, data=request_data)
        assert response.status_code == 200, response.content.decode()
        assert response.data == []

        response = self.client.get(url)
        assert response.data == []

    def test_patch_many_to_many_relationship(self):
        url = f"/entries/{self.first_entry.id}/relationships/authors"
        request_data = {
            "data": [
                {"type": format_resource_type("Author"), "id": str(self.author.id)},
            ]
        }
        response = self.client.patch(url, data=request_data)
        assert response.status_code == 200, response.content.decode()
        assert response.data == request_data["data"]

        response = self.client.get(url)
        assert response.data == request_data["data"]

        # retry a second time should end up with same result
        response = self.client.patch(url, data=request_data)
        assert response.status_code == 200, response.content.decode()
        assert response.data == request_data["data"]

        response = self.client.get(url)
        assert response.data == request_data["data"]

    def test_post_to_one_relationship_should_fail(self):
        url = f"/entries/{self.first_entry.id}/relationships/blog"
        request_data = {
            "data": {
                "type": format_resource_type("Blog"),
                "id": str(self.other_blog.id),
            }
        }
        response = self.client.post(url, data=request_data)
        assert response.status_code == 405, response.content.decode()

    def test_post_to_many_relationship_with_no_change(self):
        url = f"/entries/{self.first_entry.id}/relationships/comments"
        request_data = {
            "data": [
                {
                    "type": format_resource_type("Comment"),
                    "id": str(self.first_comment.id),
                },
            ]
        }
        response = self.client.post(url, data=request_data)
        assert response.status_code == 204, response.content.decode()
        assert len(response.rendered_content) == 0, response.rendered_content.decode()

    def test_post_to_many_relationship_with_change(self):
        url = f"/entries/{self.first_entry.id}/relationships/comments"
        request_data = {
            "data": [
                {
                    "type": format_resource_type("Comment"),
                    "id": str(self.second_comment.id),
                },
            ]
        }
        response = self.client.post(url, data=request_data)
        assert response.status_code == 200, response.content.decode()

        assert request_data["data"][0] in response.data

    def test_delete_to_one_relationship_should_fail(self):
        url = f"/entries/{self.first_entry.id}/relationships/blog"
        request_data = {
            "data": {
                "type": format_resource_type("Blog"),
                "id": str(self.other_blog.id),
            }
        }
        response = self.client.delete(url, data=request_data)
        assert response.status_code == 405, response.content.decode()

    def test_delete_relationship_overriding_with_none(self):
        url = f"/comments/{self.second_comment.id}"
        request_data = {
            "data": {
                "type": "comments",
                "id": self.second_comment.id,
                "relationships": {"author": {"data": None}},
            }
        }
        response = self.client.patch(url, data=request_data)
        assert response.status_code == 200, response.content.decode()
        assert response.data["author"] is None

    def test_delete_to_many_relationship_with_no_change(self):
        url = f"/entries/{self.first_entry.id}/relationships/comments"
        request_data = {
            "data": [
                {
                    "type": format_resource_type("Comment"),
                    "id": str(self.second_comment.id),
                },
            ]
        }
        response = self.client.delete(url, data=request_data)
        assert response.status_code == 204, response.content.decode()
        assert len(response.rendered_content) == 0, response.rendered_content.decode()

    def test_delete_one_to_many_relationship_with_not_null_constraint(self):
        url = f"/entries/{self.first_entry.id}/relationships/comments"
        request_data = {
            "data": [
                {
                    "type": format_resource_type("Comment"),
                    "id": str(self.first_comment.id),
                },
            ]
        }
        response = self.client.delete(url, data=request_data)
        assert response.status_code == 409, response.content.decode()

    def test_delete_to_many_relationship_with_change(self):
        url = f"/authors/{self.author.id}/relationships/comments"
        request_data = {
            "data": [
                {
                    "type": format_resource_type("Comment"),
                    "id": str(self.second_comment.id),
                },
            ]
        }
        response = self.client.delete(url, data=request_data)
        assert response.status_code == 200, response.content.decode()

    def test_new_comment_data_patch_to_many_relationship(self):
        entry = EntryFactory(blog=self.blog, authors=(self.author,))
        comment = CommentFactory(entry=entry)

        url = f"/authors/{self.author.id}/relationships/comments"
        request_data = {
            "data": [
                {"type": format_resource_type("Comment"), "id": str(comment.id)},
            ]
        }
        previous_response = {
            "data": [{"type": "comments", "id": str(self.second_comment.id)}],
            "links": {
                "self": "http://testserver/authors/{}/relationships/comments".format(
                    self.author.id
                )
            },
        }

        response = self.client.get(url)
        assert response.status_code == 200
        assert response.json() == previous_response

        new_patched_response = {
            "data": [{"type": "comments", "id": str(comment.id)}],
            "links": {
                "self": "http://testserver/authors/{}/relationships/comments".format(
                    self.author.id
                )
            },
        }

        response = self.client.patch(url, data=request_data)
        assert response.status_code == 200
        assert response.json() == new_patched_response

        assert Comment.objects.filter(id=self.second_comment.id).exists()

    def test_options_entry_relationship_blog(self):
        url = reverse(
            "entry-relationships",
            kwargs={"pk": self.first_entry.id, "related_field": "blog"},
        )
        response = self.client.options(url)
        expected_data = {
            "data": {
                "name": "Entry Relationship",
                "description": "",
                "renders": ["application/vnd.api+json", "text/html"],
                "parses": [
                    "application/vnd.api+json",
                    "application/x-www-form-urlencoded",
                    "multipart/form-data",
                ],
                "allowed_methods": [
                    "GET",
                    "POST",
                    "PATCH",
                    "DELETE",
                    "HEAD",
                    "OPTIONS",
                ],
                "actions": {"POST": {}},
            }
        }
        assert response.json() == expected_data


class TestRelatedMixin(APITestCase):
    def setUp(self):
        self.author = AuthorFactory()

    def _get_view(self, kwargs):
        factory = APIRequestFactory()
        request = Request(factory.get("", content_type="application/vnd.api+json"))
        return AuthorViewSet(request=request, kwargs=kwargs)

    def test_get_related_field_name(self):
        kwargs = {"pk": self.author.id, "related_field": "bio"}
        view = self._get_view(kwargs)
        got = view.get_related_field_name()
        self.assertEqual(got, kwargs["related_field"])

    def test_get_related_instance_serializer_field(self):
        kwargs = {"pk": self.author.id, "related_field": "bio"}
        view = self._get_view(kwargs)
        got = view.get_related_instance()
        self.assertEqual(got, self.author.bio)

    def test_get_related_instance_model_field(self):
        kwargs = {"pk": self.author.id, "related_field": "id"}
        view = self._get_view(kwargs)
        got = view.get_related_instance()
        self.assertEqual(got, self.author.id)

    def test_get_related_serializer_class(self):
        kwargs = {"pk": self.author.id, "related_field": "bio"}
        view = self._get_view(kwargs)
        got = view.get_related_serializer_class()
        self.assertEqual(got, AuthorBioSerializer)

    def test_get_related_serializer_class_many(self):
        kwargs = {"pk": self.author.id, "related_field": "entries"}
        view = self._get_view(kwargs)
        got = view.get_related_serializer_class()
        self.assertEqual(got, EntrySerializer)

    def test_get_serializer_comes_from_included_serializers(self):
        kwargs = {"pk": self.author.id, "related_field": "author_type"}
        view = self._get_view(kwargs)
        related_serializers = view.get_serializer_class().related_serializers
        delattr(view.get_serializer_class(), "related_serializers")
        got = view.get_related_serializer_class()
        self.assertEqual(got, AuthorTypeSerializer)
        view.get_serializer_class().related_serializers = related_serializers

    def test_get_related_serializer_class_raises_error(self):
        kwargs = {"pk": self.author.id, "related_field": "unknown"}
        view = self._get_view(kwargs)
        self.assertRaises(NotFound, view.get_related_serializer_class)

    def test_retrieve_related_single_reverse_lookup(self):
        url = reverse(
            "author-related", kwargs={"pk": self.author.pk, "related_field": "bio"}
        )
        resp = self.client.get(url, data={"include": "metadata"})
        expected = {
            "data": {
                "type": "authorBios",
                "id": str(self.author.bio.id),
                "relationships": {
                    "author": {"data": {"type": "authors", "id": str(self.author.id)}},
                    "metadata": {
                        "data": {
                            "id": str(self.author.bio.metadata.id),
                            "type": "authorBioMetadata",
                        }
                    },
                },
                "attributes": {"body": str(self.author.bio.body)},
            },
            "included": [
                {
                    "attributes": {"body": str(self.author.bio.metadata.body)},
                    "id": str(self.author.bio.metadata.id),
                    "type": "authorBioMetadata",
                }
            ],
        }
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), expected)

    def test_retrieve_related_single(self):
        url = reverse(
            "author-related",
            kwargs={"pk": self.author.author_type.pk, "related_field": "author_type"},
        )
        resp = self.client.get(url)
        expected = {
            "data": {
                "type": "authorTypes",
                "id": str(self.author.author_type.id),
                "attributes": {"name": str(self.author.author_type.name)},
            }
        }
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), expected)

    def test_retrieve_related_many(self):
        entry = EntryFactory(authors=self.author)
        url = reverse(
            "author-related", kwargs={"pk": self.author.pk, "related_field": "entries"}
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(isinstance(resp.json()["data"], list))
        self.assertEqual(len(resp.json()["data"]), 1)
        self.assertEqual(resp.json()["data"][0]["id"], str(entry.id))

    def test_retrieve_related_many_hyperlinked(self):
        comment = CommentFactory(author=self.author)
        url = reverse(
            "author-related", kwargs={"pk": self.author.pk, "related_field": "comments"}
        )
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(isinstance(resp.json()["data"], list))
        self.assertEqual(len(resp.json()["data"]), 1)
        self.assertEqual(resp.json()["data"][0]["id"], str(comment.id))

    def test_retrieve_related_None(self):
        kwargs = {"pk": self.author.pk, "related_field": "first_entry"}
        url = reverse("author-related", kwargs=kwargs)
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"data": None})

    @override_settings(JSON_API_FORMAT_RELATED_LINKS="dasherize")
    def test_retrieve_related_with_formatted_link(self):
        first_entry = EntryFactory(authors=(self.author,))

        kwargs = {"pk": self.author.pk, "related_field": "first-entry"}
        url = reverse("author-related", kwargs=kwargs)
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["data"]["id"], str(first_entry.id))


class TestValidationErrorResponses(TestBase):
    def test_if_returns_error_on_empty_post(self):
        view = BlogViewSet.as_view({"post": "create"})
        response = self._get_create_response("{}", view)
        self.assertEqual(400, response.status_code)
        expected = [
            {
                "detail": "Received document does not contain primary data",
                "status": "400",
                "source": {"pointer": "/data"},
                "code": "parse_error",
            }
        ]
        self.assertEqual(expected, response.data)

    def test_if_returns_error_on_missing_form_data_post(self):
        view = BlogViewSet.as_view({"post": "create"})
        response = self._get_create_response(
            '{"data":{"attributes":{},"type":"blogs"}}', view
        )
        self.assertEqual(400, response.status_code)
        expected = [
            {
                "status": "400",
                "detail": "This field is required.",
                "source": {"pointer": "/data/attributes/name"},
                "code": "required",
            }
        ]
        self.assertEqual(expected, response.data)

    def test_if_returns_error_on_bad_endpoint_name(self):
        view = BlogViewSet.as_view({"post": "create"})
        response = self._get_create_response(
            '{"data":{"attributes":{},"type":"bad"}}', view
        )
        self.assertEqual(409, response.status_code)
        expected = [
            {
                "detail": (
                    "The resource object's type (bad) is not the type that constitute the collection "
                    "represented by the endpoint (blogs)."
                ),
                "source": {"pointer": "/data"},
                "status": "409",
                "code": "error",
            }
        ]
        self.assertEqual(expected, response.data)

    def _get_create_response(self, data, view):
        factory = RequestFactory()
        request = factory.post("/", data, content_type="application/vnd.api+json")
        user = self.create_user("user", "pass")
        force_authenticate(request, user)
        return view(request)


class TestModelViewSet(TestBase):
    def setUp(self):
        self.author = Author.objects.create(
            name="Super powerful superhero", email="i.am@lost.com"
        )
        self.blog = Blog.objects.create(name="Some Blog", tagline="It's a blog")

    def test_no_content_response(self):
        url = f"/blogs/{self.blog.pk}"
        response = self.client.delete(url)
        assert response.status_code == 204, response.rendered_content.decode()
        assert len(response.rendered_content) == 0, response.rendered_content.decode()


class TestBlogViewSet(APITestCase):
    def setUp(self):
        self.blog = Blog.objects.create(name="Some Blog", tagline="It's a blog")
        self.entry = Entry.objects.create(
            blog=self.blog,
            headline="headline one",
            body_text="body_text two",
        )

    def test_get_object_gives_correct_blog(self):
        url = reverse("entry-blog", kwargs={"entry_pk": self.entry.id})
        resp = self.client.get(url)
        expected = {
            "data": {
                "attributes": {"name": self.blog.name},
                "id": f"{self.blog.id}",
                "links": {"self": f"http://testserver/blogs/{self.blog.id}"},
                "meta": {"copyright": datetime.now().year},
                "relationships": {"tags": {"data": [], "meta": {"count": 0}}},
                "type": "blogs",
            },
            "meta": {"apiDocs": "/docs/api/blogs"},
        }
        got = resp.json()
        self.assertEqual(got, expected)


class TestEntryViewSet(APITestCase):
    def setUp(self):
        self.blog = Blog.objects.create(name="Some Blog", tagline="It's a blog")
        self.first_entry = Entry.objects.create(
            blog=self.blog,
            headline="headline two",
            body_text="body_text two",
        )
        self.second_entry = Entry.objects.create(
            blog=self.blog,
            headline="headline two",
            body_text="body_text two",
        )
        self.maxDiff = None

    def test_get_object_gives_correct_entry(self):
        url = reverse("entry-featured", kwargs={"entry_pk": self.first_entry.id})
        resp = self.client.get(url)
        expected = {
            "data": {
                "attributes": {
                    "bodyText": self.second_entry.body_text,
                    "headline": self.second_entry.headline,
                    "modDate": self.second_entry.mod_date,
                    "pubDate": self.second_entry.pub_date,
                },
                "id": f"{self.second_entry.id}",
                "meta": {"bodyFormat": "text"},
                "relationships": {
                    "authors": {"data": [], "meta": {"count": 0}},
                    "blog": {
                        "data": {
                            "id": f"{self.second_entry.blog_id}",
                            "type": "blogs",
                        }
                    },
                    "blogHyperlinked": {
                        "links": {
                            "related": "http://testserver/entries/{}"
                            "/blog".format(self.second_entry.id),
                            "self": "http://testserver/entries/{}"
                            "/relationships/blog_hyperlinked".format(
                                self.second_entry.id
                            ),
                        }
                    },
                    "comments": {"data": [], "meta": {"count": 0}},
                    "commentsHyperlinked": {
                        "links": {
                            "related": "http://testserver/entries/{}"
                            "/comments".format(self.second_entry.id),
                            "self": "http://testserver/entries/{}/relationships"
                            "/comments_hyperlinked".format(self.second_entry.id),
                        }
                    },
                    "featuredHyperlinked": {
                        "links": {
                            "related": "http://testserver/entries/{}"
                            "/featured".format(self.second_entry.id),
                            "self": "http://testserver/entries/{}/relationships"
                            "/featured_hyperlinked".format(self.second_entry.id),
                        }
                    },
                    "suggested": {
                        "data": [{"id": "1", "type": "entries"}],
                        "links": {
                            "related": "http://testserver/entries/{}"
                            "/suggested/".format(self.second_entry.id),
                            "self": "http://testserver/entries/{}"
                            "/relationships/suggested".format(self.second_entry.id),
                        },
                    },
                    "suggestedHyperlinked": {
                        "links": {
                            "related": "http://testserver/entries/{}"
                            "/suggested/".format(self.second_entry.id),
                            "self": "http://testserver/entries/{}/relationships"
                            "/suggested_hyperlinked".format(self.second_entry.id),
                        }
                    },
                    "tags": {"data": [], "meta": {"count": 0}},
                },
                "type": "posts",
            }
        }
        got = resp.json()
        self.assertEqual(got, expected)


class BasicAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ("name",)


class ReadOnlyViewSetWithCustomActions(views.ReadOnlyModelViewSet):
    queryset = Author.objects.all()
    serializer_class = BasicAuthorSerializer

    @action(detail=False, methods=["get", "post", "patch", "delete"])
    def group_action(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get", "post", "patch", "delete"])
    def item_action(self, request, pk):
        return Response(status=status.HTTP_204_NO_CONTENT)


class TestReadonlyModelViewSet(TestBase):
    """
    Test if ReadOnlyModelViewSet allows to have custom actions with POST, PATCH, DELETE methods
    """

    factory = RequestFactory()
    viewset_class = ReadOnlyViewSetWithCustomActions
    media_type = "application/vnd.api+json"

    def test_group_action_allows_get(self):
        view = self.viewset_class.as_view({"get": "group_action"})
        request = self.factory.get("/")
        response = view(request)
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

    def test_group_action_allows_post(self):
        view = self.viewset_class.as_view({"post": "group_action"})
        request = self.factory.post("/", "{}", content_type=self.media_type)
        response = view(request)
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

    def test_group_action_allows_patch(self):
        view = self.viewset_class.as_view({"patch": "group_action"})
        request = self.factory.patch("/", "{}", content_type=self.media_type)
        response = view(request)
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

    def test_group_action_allows_delete(self):
        view = self.viewset_class.as_view({"delete": "group_action"})
        request = self.factory.delete("/", "{}", content_type=self.media_type)
        response = view(request)
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

    def test_item_action_allows_get(self):
        view = self.viewset_class.as_view({"get": "item_action"})
        request = self.factory.get("/")
        response = view(request, pk="1")
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

    def test_item_action_allows_post(self):
        view = self.viewset_class.as_view({"post": "item_action"})
        request = self.factory.post("/", "{}", content_type=self.media_type)
        response = view(request, pk="1")
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

    def test_item_action_allows_patch(self):
        view = self.viewset_class.as_view({"patch": "item_action"})
        request = self.factory.patch("/", "{}", content_type=self.media_type)
        response = view(request, pk="1")
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

    def test_item_action_allows_delete(self):
        view = self.viewset_class.as_view({"delete": "item_action"})
        request = self.factory.delete("/", "{}", content_type=self.media_type)
        response = view(request, pk="1")
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
