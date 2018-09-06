from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from ..models import Blog, Entry


class DJATestFilters(APITestCase):
    """
    tests of JSON:API filter backends
    """
    fixtures = ('blogentry',)

    def setUp(self):
        self.entries = Entry.objects.all()
        self.blogs = Blog.objects.all()
        self.url = reverse('nopage-entry-list')
        self.fs_url = reverse('filterset-entry-list')
        self.no_fs_url = reverse('nofilterset-entry-list')

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

    def test_filter_exact(self):
        """
        filter for an exact match
        """
        response = self.client.get(self.url, data={'filter[headline]': 'CHEM3271X'})
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(len(dja_response['data']), 1)

    def test_filter_exact_fail(self):
        """
        failed search for an exact match
        """
        response = self.client.get(self.url, data={'filter[headline]': 'XXXXX'})
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(len(dja_response['data']), 0)

    def test_filter_isnull(self):
        """
        search for null value
        """
        response = self.client.get(self.url, data={'filter[bodyText.isnull]': 'true'})
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(
            len(dja_response['data']),
            len([k for k in self.entries if k.body_text is None])
        )

    def test_filter_not_null(self):
        """
        search for not null
        """
        response = self.client.get(self.url, data={'filter[bodyText.isnull]': 'false'})
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(
            len(dja_response['data']),
            len([k for k in self.entries if k.body_text is not None])
        )

    def test_filter_isempty(self):
        """
        search for an empty value (different from null!)
        the easiest way to do this is search for r'^$'
        """
        response = self.client.get(self.url, data={'filter[bodyText.regex]': '^$'})
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(len(dja_response['data']),
                         len([k for k in self.entries
                              if k.body_text is not None and
                              len(k.body_text) == 0]))

    def test_filter_related(self):
        """
        filter via a relationship chain
        """
        response = self.client.get(self.url, data={'filter[blog.name]': 'ANTB'})
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(len(dja_response['data']),
                         len([k for k in self.entries
                              if k.blog.name == 'ANTB']))

    def test_filter_related_fieldset_class(self):
        """
        filter via a FilterSet class instead of filterset_fields shortcut
        This tests a shortcut for a longer ORM path: `bname` is a shortcut
        name for `blog.name`.
        """
        response = self.client.get(self.fs_url, data={'filter[bname]': 'ANTB'})
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(len(dja_response['data']),
                         len([k for k in self.entries
                              if k.blog.name == 'ANTB']))

    def test_filter_related_missing_fieldset_class(self):
        """
        filter via with neither filterset_fields nor filterset_class
        This should return an error for any filter[]
        """
        response = self.client.get(self.no_fs_url, data={'filter[bname]': 'ANTB'})
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "invalid filter[bname]")

    def test_filter_fields_union_list(self):
        """
        test field for a list of values(ORed): ?filter[field.in]': 'val1,val2,val3
        """
        response = self.client.get(self.url,
                                   data={'filter[headline.in]': 'CLCV2442V,XXX,BIOL3594X'})
        dja_response = response.json()
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        self.assertEqual(
            len(dja_response['data']),
            len([k for k in self.entries if k.headline == 'CLCV2442V']) +
            len([k for k in self.entries if k.headline == 'XXX']) +
            len([k for k in self.entries if k.headline == 'BIOL3594X']),
            msg="filter field list (union)")

    def test_filter_fields_intersection(self):
        """
        test fields (ANDed): ?filter[field1]': 'val1&filter[field2]'='val2
        """
        #
        response = self.client.get(self.url,
                                   data={'filter[headline.regex]': '^A',
                                         'filter[body_text.icontains]': 'in'})
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertGreater(len(dja_response['data']), 1)
        self.assertEqual(
            len(dja_response['data']),
            len([k for k in self.entries if k.headline.startswith('A') and
                 'in' in k.body_text.lower()]))

    def test_filter_invalid_association_name(self):
        """
        test for filter with invalid filter association name
        """
        response = self.client.get(self.url, data={'filter[nonesuch]': 'CHEM3271X'})
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "invalid filter[nonesuch]")

    def test_filter_empty_association_name(self):
        """
        test for filter with missing association name
        """
        response = self.client.get(self.url, data={'filter[]': 'foobar'})
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "invalid filter: filter[]")

    def test_filter_no_brackets(self):
        """
        test for `filter=foobar` with missing filter[association] name
        """
        response = self.client.get(self.url, data={'filter': 'foobar'})
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "invalid filter: filter")

    def test_filter_no_brackets_rvalue(self):
        """
        test for `filter=` with missing filter[association] and value
        """
        response = self.client.get(self.url + '?filter=')
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "invalid filter: filter")

    def test_filter_no_brackets_equal(self):
        """
        test for `filter` with missing filter[association] name and =value
        """
        response = self.client.get(self.url + '?filter')
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "invalid filter: filter")

    def test_filter_malformed_left_bracket(self):
        """
        test for filter with invalid filter syntax
        """
        response = self.client.get(self.url, data={'filter[': 'foobar'})
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "invalid filter: filter[")

    def test_filter_missing_right_bracket(self):
        """
        test for filter missing right bracket
        """
        response = self.client.get(self.url, data={'filter[headline': 'foobar'})
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "invalid filter: filter[headline")

    def test_filter_missing_rvalue(self):
        """
        test for filter with missing value to test against
        this should probably be an error rather than ignoring the filter:
        https://django-filter.readthedocs.io/en/latest/guide/tips.html#filtering-by-an-empty-string
        """
        response = self.client.get(self.url, data={'filter[headline]': ''})
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "missing filter[headline] test value")

    def test_filter_missing_rvalue_equal(self):
        """
        test for filter with missing value to test against
        this should probably be an error rather than ignoring the filter:
            """
        response = self.client.get(self.url + '?filter[headline]')
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "missing filter[headline] test value")
