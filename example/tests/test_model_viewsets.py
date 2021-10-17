import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from django.utils import encoding

from example.tests import TestBase


class ModelViewSetTests(TestBase):
    """
    Test usage with ModelViewSets, also tests pluralization, camelization,
    and underscore.

    [<RegexURLPattern user-list ^identities/$>,
    <RegexURLPattern user-detail ^identities/(?P<pk>[^/]+)/$>]
    """

    list_url = reverse("user-list")

    def setUp(self):
        super().setUp()
        self.detail_url = reverse("user-detail", kwargs={"pk": self.miles.pk})

    def test_key_in_list_result(self):
        """
        Ensure the result has a 'user' key since that is the name of the model
        """
        with override_settings(JSON_API_FORMAT_FIELD_NAMES="dasherize"):
            response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

        user = get_user_model().objects.all()[0]
        expected = {
            "data": [
                {
                    "type": "users",
                    "id": encoding.force_str(user.pk),
                    "attributes": {
                        "first-name": user.first_name,
                        "last-name": user.last_name,
                        "email": user.email,
                    },
                }
            ],
            "links": {
                "first": "http://testserver/identities?page%5Bnumber%5D=1",
                "last": "http://testserver/identities?page%5Bnumber%5D=2",
                "next": "http://testserver/identities?page%5Bnumber%5D=2",
                "prev": None,
            },
            "meta": {"pagination": {"page": 1, "pages": 2, "count": 2}},
        }

        assert expected == response.json()

    def test_page_two_in_list_result(self):
        """
        Ensure that the second page is reachable and is the correct data.
        """
        with override_settings(JSON_API_FORMAT_FIELD_NAMES="dasherize"):
            response = self.client.get(self.list_url, {"page[number]": 2})
        self.assertEqual(response.status_code, 200)

        user = get_user_model().objects.all()[1]
        expected = {
            "data": [
                {
                    "type": "users",
                    "id": encoding.force_str(user.pk),
                    "attributes": {
                        "first-name": user.first_name,
                        "last-name": user.last_name,
                        "email": user.email,
                    },
                }
            ],
            "links": {
                "first": "http://testserver/identities?page%5Bnumber%5D=1",
                "last": "http://testserver/identities?page%5Bnumber%5D=2",
                "next": None,
                "prev": "http://testserver/identities?page%5Bnumber%5D=1",
            },
            "meta": {"pagination": {"page": 2, "pages": 2, "count": 2}},
        }

        assert expected == response.json()

    def test_page_range_in_list_result(self):
        """
        Ensure that the range of a page can be changed from the client,
        tests pluralization as two objects means it converts ``user`` to
        ``users``.
        """
        with override_settings(JSON_API_FORMAT_FIELD_NAMES="dasherize"):
            response = self.client.get(self.list_url, {"page[size]": 2})
        self.assertEqual(response.status_code, 200)

        users = get_user_model().objects.all()
        expected = {
            "data": [
                {
                    "type": "users",
                    "id": encoding.force_str(users[0].pk),
                    "attributes": {
                        "first-name": users[0].first_name,
                        "last-name": users[0].last_name,
                        "email": users[0].email,
                    },
                },
                {
                    "type": "users",
                    "id": encoding.force_str(users[1].pk),
                    "attributes": {
                        "first-name": users[1].first_name,
                        "last-name": users[1].last_name,
                        "email": users[1].email,
                    },
                },
            ],
            "links": {
                "first": "http://testserver/identities?page%5Bnumber%5D=1&page%5Bsize%5D=2",
                "last": "http://testserver/identities?page%5Bnumber%5D=1&page%5Bsize%5D=2",
                "next": None,
                "prev": None,
            },
            "meta": {"pagination": {"page": 1, "pages": 1, "count": 2}},
        }

        assert expected == response.json()

    def test_key_in_detail_result(self):
        """
        Ensure the result has a 'user' key.
        """
        with override_settings(JSON_API_FORMAT_FIELD_NAMES="dasherize"):
            response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

        expected = {
            "data": {
                "type": "users",
                "id": encoding.force_str(self.miles.pk),
                "attributes": {
                    "first-name": self.miles.first_name,
                    "last-name": self.miles.last_name,
                    "email": self.miles.email,
                },
            }
        }

        assert expected == response.json()

    def test_patch_requires_id(self):
        """
        Verify that 'id' is required to be passed in an update request.
        """
        data = {
            "data": {"type": "users", "attributes": {"first-name": "DifferentName"}}
        }

        response = self.client.patch(self.detail_url, data=data)

        self.assertEqual(response.status_code, 400)

    def test_patch_requires_correct_id(self):
        """
        Verify that 'id' is the same then in url
        """
        data = {
            "data": {
                "type": "users",
                "id": self.miles.pk + 1,
                "attributes": {"first-name": "DifferentName"},
            }
        }

        response = self.client.patch(self.detail_url, data=data)

        self.assertEqual(response.status_code, 409)

    def test_key_in_post(self):
        """
        Ensure a key is in the post.
        """
        self.client.login(username="miles", password="pw")
        data = {
            "data": {
                "type": "users",
                "id": encoding.force_str(self.miles.pk),
                "attributes": {
                    "first-name": self.miles.first_name,
                    "last-name": self.miles.last_name,
                    "email": "miles@trumpet.org",
                },
            }
        }

        with override_settings(JSON_API_FORMAT_FIELD_NAMES="dasherize"):
            response = self.client.put(self.detail_url, data=data)

        assert data == response.json()

        # is it updated?
        self.assertEqual(
            get_user_model().objects.get(pk=self.miles.pk).email, "miles@trumpet.org"
        )

    def test_404_error_pointer(self):
        self.client.login(username="miles", password="pw")
        not_found_url = reverse("user-detail", kwargs={"pk": 12345})
        errors = {
            "errors": [{"detail": "Not found.", "status": "404", "code": "not_found"}]
        }

        response = self.client.get(not_found_url)
        assert 404 == response.status_code
        assert errors == response.json()


@pytest.mark.django_db
def test_patch_allow_field_type(author, author_type_factory, client):
    """
    Verify that type field may be updated.
    """
    # TODO remove in next major version 5.0.0 see serializers.ReservedFieldNamesMixin
    with pytest.deprecated_call():
        author_type = author_type_factory()
        url = reverse("author-detail", args=[author.id])

        data = {
            "data": {
                "id": author.id,
                "type": "authors",
                "relationships": {
                    "data": {"id": author_type.id, "type": "author-type"}
                },
            }
        }

        response = client.patch(url, data=data)

        assert response.status_code == 200
