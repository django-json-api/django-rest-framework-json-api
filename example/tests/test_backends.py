import json

from rest_framework.test import APITestCase

from ..models import Blog, Entry

ENTRIES = "/nopage-entries"


class DJATestParameters(APITestCase):
    """
    tests of JSON:API backends
    """
    fixtures = ('blogentry',)

    def setUp(self):
        self.entries = Entry.objects.all()
        self.blogs = Blog.objects.all()

    def test_sort(self):
        """
        test sort
        """
        response = self.client.get(ENTRIES + '?sort=headline')
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        j = json.loads(response.content.decode("utf-8"))
        headlines = [c['attributes']['headline'] for c in j['data']]
        sorted_headlines = [c['attributes']['headline'] for c in j['data']]
        sorted_headlines.sort()
        self.assertEqual(headlines, sorted_headlines)

    def test_sort_reverse(self):
        """
        confirm switching the sort order actually works
        """
        response = self.client.get(ENTRIES + '?sort=-headline')
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        j = json.loads(response.content.decode("utf-8"))
        headlines = [c['attributes']['headline'] for c in j['data']]
        sorted_headlines = [c['attributes']['headline'] for c in j['data']]
        sorted_headlines.sort()
        self.assertNotEqual(headlines, sorted_headlines)

    def test_sort_invalid(self):
        """
        test sort of invalid field
        """
        response = self.client.get(
            ENTRIES + '?sort=nonesuch,headline,-not_a_field')
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        j = json.loads(response.content.decode("utf-8"))
        self.assertEqual(j['errors'][0]['detail'],
                         "invalid sort parameters: nonesuch,-not_a_field")
