from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class TestBase(APITestCase):
    """
    Test base class to setup a couple users.
    """

    def setUp(self):
        """
        Create those users
        """
        super().setUp()
        self.create_users()

    def create_user(self, username, email, password="pw", first_name="", last_name=""):
        """
        Helper method to create a user
        """
        User = get_user_model()
        user = User.objects.create_user(username, email, password=password)
        if first_name or last_name:
            user.first_name = first_name
            user.last_name = last_name
            user.save()
        return user

    def create_users(self):
        """
        Create a couple users
        """
        self.john = self.create_user(
            "trane", "john@example.com", first_name="John", last_name="Coltrane"
        )
        self.miles = self.create_user(
            "miles", "miles@example.com", first_name="Miles", last_name="Davis"
        )
