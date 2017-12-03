"""
Test sideloading resources
"""
import json

import django
from django.utils import encoding

if django.VERSION >= (1, 10):
    from django.urls import reverse
else:
    from django.core.urlresolvers import reverse

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
            [encoding.force_text('identities'),
             encoding.force_text('posts')])
