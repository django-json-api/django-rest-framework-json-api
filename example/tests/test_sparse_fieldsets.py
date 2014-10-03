

import json
from example.tests import TestBase
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse, reverse_lazy
from django.conf import settings


class SparseModelViewsetTests(TestBase):
    """

    """
    list_url = reverse_lazy('user-list')

    def setUp(self):
        super(SparseModelViewsetTests, self).setUp()
        self.detail_url = reverse('user-detail', kwargs={'pk': self.miles.pk})

    def test_get_id_and_email_in_list_view(self):
        """
        Ensure that in the list view, the ``fields`` query param
        limits the fields returned.
        """
        url = "{0}?fields=id,email".format(self.list_url)

        response = self.client.get(url)
        json_content = json.loads(response.content)

        self.assertEqual(
            json_content['user'][0].keys(),
            ['id', 'email'])

    def test_get_id_and_email_in_detail_view(self):
        """
        Ensure only what is specified is returned on the detail view
        when the ``fields`` query param is present
        """
        url = "{0}?fields=id,email".format(self.detail_url)
        response = self.client.get(url)
        self.assertEqual(
            response.data.keys(),
            ['id', 'email'])

