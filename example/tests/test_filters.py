from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from ..models import Blog, Entry


class DJATestParameters(APITestCase):
    """
    tests of JSON:API backends
    """
    fixtures = ('blogentry',)

    def setUp(self):
        self.entries = Entry.objects.all()
        self.blogs = Blog.objects.all()
        self.url = reverse('nopage-entry-list')

    def test_sort(self):
        """
        test sort
        """
        response = self.client.get(self.url, data={'sort': 'headline'})
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        headlines = [c['attributes']['headline'] for c in dja_response['data']]
        sorted_headlines = [c['attributes']['headline'] for c in dja_response['data']]
        sorted_headlines.sort()
        self.assertEqual(headlines, sorted_headlines)

    def test_sort_reverse(self):
        """
        confirm switching the sort order actually works
        """
        response = self.client.get(self.url, data={'sort': '-headline'})
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        headlines = [c['attributes']['headline'] for c in dja_response['data']]
        sorted_headlines = [c['attributes']['headline'] for c in dja_response['data']]
        sorted_headlines.sort()
        self.assertNotEqual(headlines, sorted_headlines)

    def test_sort_invalid(self):
        """
        test sort of invalid field
        """
        response = self.client.get(self.url,
                                   data={'sort': 'nonesuch,headline,-not_a_field'})
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "invalid sort parameters: nonesuch,-not_a_field")
