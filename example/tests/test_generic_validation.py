from django.urls import reverse

from example.tests import TestBase


class GenericValidationTest(TestBase):
    """
    Test that a non serializer specific validation can be thrown and formatted
    """

    def setUp(self):
        super().setUp()
        self.url = reverse("user-validation", kwargs={"pk": self.miles.pk})

    def test_generic_validation_error(self):
        """
        Check error formatting
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)

        expected = {
            "errors": [
                {
                    "status": "400",
                    "source": {"pointer": "/data"},
                    "detail": "Oh nohs!",
                    "code": "invalid",
                }
            ]
        }

        assert expected == response.json()
