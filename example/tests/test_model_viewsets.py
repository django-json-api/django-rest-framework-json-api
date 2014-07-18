

import json
from example.tests import TestBase
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse, reverse_lazy
from django.conf import settings


class ModelViewSetTests(TestBase):
    """
    Test usage with ModelViewSets

    [<RegexURLPattern user-list ^user-viewsets/$>, <RegexURLPattern user-detail ^user-viewsets/(?P<pk>[^/]+)/$>]
    """
    list_url = reverse_lazy('user-list')

    def setUp(self):
        super(ModelViewSetTests, self).setUp()
        self.detail_url = reverse('user-detail', kwargs={'pk': self.miles.pk})

    def test_key_in_list_result(self):
        """
        Ensure the result has a "user" key since that is the name of the model
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

        expected = {"user": []}
        for user in get_user_model().objects.all():
            expected['user'].append({
                'id': user.pk,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email})

        self.assertEquals(expected, json.loads(response.content))

    def test_key_in_detail_result(self):
        """
        Ensure the result has a "user" key.
        """
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.content)
        expected = {
            'user': {
                'id': self.miles.pk,
                'first_name': self.miles.first_name,
                'last_name': self.miles.last_name,
                'email': self.miles.email
            }
        }

        self.assertEqual(result, expected)

    def test_key_in_post(self):
        """
        Ensure a key is in the post.
        """
        self.client.login(username='miles', password='pw')
        data = {
            'user': {
                'id': self.miles.pk,
                'first_name': self.miles.first_name,
                'last_name': self.miles.last_name,
                'email': 'miles@trumpet.org'
            }
        }
        response = self.client.put(self.detail_url, data=data, format='json')

        result = json.loads(response.content)

        self.assertIn('user', result.keys())
        self.assertEqual(result['user']['email'], 'miles@trumpet.org')

        # is it updated?
        self.assertEqual(
            get_user_model().objects.get(pk=self.miles.pk).email,
            'miles@trumpet.org')

