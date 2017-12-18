import json

from django.urls import reverse
from django.utils import encoding

from example.tests import TestBase


class MultipleIDMixin(TestBase):
    """
    Test usage with MultipleIDMixin

    [<RegexURLPattern user-list ^user-viewsets/$>,
     <RegexURLPattern user-detail ^user-viewsets/(?P<pk>[^/]+)/$>]
    """
    list_url = reverse('user-list')

    def test_single_id_in_query_params(self):
        """
        Ensure single ID in query params returns correct result
        """
        url = '/identities?ids[]={0}'.format(self.miles.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        expected = {
            'data': {
                'type': 'users',
                'id': encoding.force_text(self.miles.pk),
                'attributes': {
                    'first_name': self.miles.first_name,
                    'last_name': self.miles.last_name,
                    'email': self.miles.email
                }
            }
        }

        json_content = json.loads(response.content.decode('utf8'))
        links = json_content.get("links")
        meta = json_content.get("meta").get('pagination')

        self.assertEquals(expected.get('user'), json_content.get('user'))
        self.assertEquals(meta.get('count', 0), 1)
        self.assertEquals(links.get("next"), None)
        self.assertEqual(meta.get("page"), 1)

    def test_multiple_ids_in_query_params(self):
        """
        Ensure multiple IDs in query params return correct result
        """
        url = '/identities?ids[]={0}&ids[]={1}'.format(
            self.miles.pk, self.john.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        expected = {
            'data': {
                'type': 'users',
                'id': encoding.force_text(self.john.pk),
                'attributes': {
                    'first_name': self.john.first_name,
                    'last_name': self.john.last_name,
                    'email': self.john.email
                }
            }
        }

        json_content = json.loads(response.content.decode('utf8'))
        links = json_content.get("links")
        meta = json_content.get("meta").get('pagination')

        self.assertEquals(expected.get('user'), json_content.get('user'))
        self.assertEquals(meta.get('count', 0), 2)
        self.assertEqual(
            sorted(
                'http://testserver/identities?ids%5B%5D=2&ids%5B%5D=1&page=2'
                .split('?')[1].split('&')
            ),
            sorted(
                links.get("next").split('?')[1].split('&'))
        )
        self.assertEqual(meta.get("page"), 1)
