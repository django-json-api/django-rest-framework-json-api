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
        sorted_headlines = sorted(headlines)
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
        sorted_headlines = sorted(headlines)
        self.assertNotEqual(headlines, sorted_headlines)

    def test_sort_double_negative(self):
        """
        what if they provide multiple `-`'s? It's OK.
        """
        response = self.client.get(self.url, data={'sort': '--headline'})
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        headlines = [c['attributes']['headline'] for c in dja_response['data']]
        sorted_headlines = sorted(headlines)
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

    def test_sort_camelcase(self):
        """
        test sort of camelcase field name
        """
        response = self.client.get(self.url, data={'sort': 'bodyText'})
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        blog_ids = [(c['attributes']['bodyText'] or '') for c in dja_response['data']]
        sorted_blog_ids = sorted(blog_ids)
        self.assertEqual(blog_ids, sorted_blog_ids)

    def test_sort_underscore(self):
        """
        test sort of underscore field name
        Do we allow this notation in a search even if camelcase is in effect?
        "Be conservative in what you send, be liberal in what you accept"
                   --  https://en.wikipedia.org/wiki/Robustness_principle
        """
        response = self.client.get(self.url, data={'sort': 'body_text'})
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        blog_ids = [(c['attributes']['bodyText'] or '') for c in dja_response['data']]
        sorted_blog_ids = sorted(blog_ids)
        self.assertEqual(blog_ids, sorted_blog_ids)

    def test_sort_related(self):
        """
        test sort via related field using jsonapi path `.` and django orm `__` notation.
        ORM relations must be predefined in the View's .ordering_fields attr
        """
        for datum in ('blog__id', 'blog.id'):
            response = self.client.get(self.url, data={'sort': datum})
            self.assertEqual(response.status_code, 200,
                             msg=response.content.decode("utf-8"))
            dja_response = response.json()
            blog_ids = [c['relationships']['blog']['data']['id'] for c in dja_response['data']]
            sorted_blog_ids = sorted(blog_ids)
            self.assertEqual(blog_ids, sorted_blog_ids)
