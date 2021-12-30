from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import encoding
from rest_framework import status

from example.tests import TestBase


class FormatKeysSetTests(TestBase):
    """
    Test that camelization and underscoring of key names works if they are activated.
    """

    list_url = reverse("user-list")

    def setUp(self):
        super().setUp()
        self.detail_url = reverse("user-detail", kwargs={"pk": self.miles.pk})

    def test_camelization(self):
        """
        Test that camelization works.
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

        user = get_user_model().objects.all()[0]
        expected = {
            "data": [
                {
                    "type": "users",
                    "id": encoding.force_str(user.pk),
                    "attributes": {
                        "firstName": user.first_name,
                        "lastName": user.last_name,
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


def test_options_format_field_names(db, client):
    response = client.options(reverse("author-list"))
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    expected_keys = {
        "name",
        "email",
        "bio",
        "entries",
        "firstEntry",
        "authorType",
        "comments",
        "secrets",
        "defaults",
        "initials",
    }
    assert expected_keys == data["actions"]["POST"].keys()
