

import json
from example.tests import TestBase
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse, reverse_lazy
from django.conf import settings


class EmberDataModelMixinTests(TestBase):
    """
    Test usage with EmberDataModelMixin

    [<RegexURLPattern user-list ^user-viewsets/$>, <RegexURLPattern user-detail ^user-viewsets/(?P<pk>[^/]+)/$>]
    """
    list_url = reverse_lazy('user-list')

    def setUp(self):
        super(EmberDataModelMixinTests, self).setUp()
        self.detail_url = '/user-mixin-viewset/?ids[]=%s' % self.miles.pk

    def test_single_id_in_query_params(self):
        """
        Ensure the result has a "user" key.
        """
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

        expected = {
            'user': [{
                'id': self.miles.pk,
                'first_name': self.miles.first_name,
                'last_name': self.miles.last_name,
                'email': self.miles.email
            }]
        }

        json_content = json.loads(response.content)
        meta = json_content.get("meta")

        self.assertEquals(expected.get('user'), json_content.get('user'))
        self.assertEquals(meta.get('count', 0), 1)
        self.assertEquals(meta.get("next"), None)
        self.assertEqual(None, meta.get("next_link"))
        self.assertEqual(meta.get("page"), 1)

    def test_multiple_ids_in_query_params(self):
        """
        Ensure the result has a "user" key.
        """
        url = '/user-mixin-viewset/?ids[]=%s&ids[]=%s' % (self.miles.pk, self.john.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        expected = {
            'user': [{
                'id': self.john.pk,
                'first_name': self.john.first_name,
                'last_name': self.john.last_name,
                'email': self.john.email
            }]
        }

        json_content = json.loads(response.content)
        meta = json_content.get("meta")

        self.assertEquals(expected.get('user'), json_content.get('user'))
        self.assertEquals(meta.get('count', 0), 2)
        self.assertEquals(meta.get("next"), 2)
        self.assertEqual('http://testserver/user-mixin-viewset/?ids%5B%5D=2&ids%5B%5D=1&page=2', meta.get("next_link"))
        self.assertEqual(meta.get("page"), 1)
