"""
Test sideloading resources
"""
import json
from example.tests import TestBase
from django.core.urlresolvers import reverse_lazy
from django.conf import settings


class SideloadResourceTest(TestBase):
    """
    Test that sideloading resources returns expected output.
    """
    url = reverse_lazy('users-cars')

    def test_get_sideloaded_data(self):
        """
        Ensure resources that are meant for sideloaded data
        do not return a single root key.
        """
        response = self.client.get(self.url)
        content = json.loads(response.content)

        self.assertEqual(content.keys(), ['cars', 'users'])

