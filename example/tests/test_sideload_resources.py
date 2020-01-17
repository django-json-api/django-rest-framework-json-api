"""
Test sideloading resources
"""
import json

from django.urls import reverse
from django.utils import encoding

from example.tests import TestBase


class SideloadResourceTest(TestBase):
    """
    Test that sideloading resources returns expected output.
    """
    url = reverse('user-posts')

    def test_get_sideloaded_data(self):
        """
        Ensure resources that are meant for sideloaded data
        do not return a single root key.
        """
        response = self.client.get(self.url)
        content = json.loads(response.content.decode('utf8'))

        self.assertEqual(
            sorted(content.keys()),
            [encoding.force_str('identities'),
             encoding.force_str('posts')])
