from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from example.models import Blog, Entry


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
        error texts are different depending on whether QueryParameterValidationFilter is in use.
        """
        response = self.client.get(self.url, data={'filter[]': 'foobar'})
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'], "invalid query parameter: filter[]")

    def test_filter_no_brackets(self):
        """
        test for `filter=foobar` with missing filter[association] name
        """
        response = self.client.get(self.url, data={'filter': 'foobar'})
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "invalid query parameter: filter")

    def test_filter_missing_right_bracket(self):
        """
        test for filter missing right bracket
        """
        response = self.client.get(self.url, data={'filter[headline': 'foobar'})
        self.assertEqual(response.status_code, 400, msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "invalid query parameter: filter[headline")

    def test_filter_no_brackets_rvalue(self):
        """
        test for `filter=` with missing filter[association] and value
        """
        response = self.client.get(self.url + '?filter=')
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "invalid query parameter: filter")

    def test_filter_no_brackets_equal(self):
        """
        test for `filter` with missing filter[association] name and =value
        """
        response = self.client.get(self.url + '?filter')
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "invalid query parameter: filter")

    def test_filter_malformed_left_bracket(self):
        """
        test for filter with invalid filter syntax
        """
        response = self.client.get(self.url, data={'filter[': 'foobar'})
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'], "invalid query parameter: filter[")

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

    def test_search_keywords(self):
        """
        test for `filter[search]="keywords"` where some of the keywords are in the entry and
        others are in the related blog.
        """
        response = self.client.get(self.url, data={'filter[search]': 'barnard field research'})
        expected_result = {
            'data': [
                {
                    'type': 'posts',
                    'id': '7',
                    'attributes': {
                        'headline': 'ANTH3868X',
                        'bodyText': 'ETHNOGRAPHIC FIELD RESEARCH IN NYC',
                        'pubDate': None,
                        'modDate': None},
                    'relationships': {
                        'blog': {
                            'data': {
                                'type': 'blogs',
                                'id': '1'
                            }
                        },
                        'blogHyperlinked': {
                            'links': {
                                'self': 'http://testserver/entries/7/relationships/blog_hyperlinked',  # noqa: E501
                                'related': 'http://testserver/entries/7/blog'}
                        },
                        'authors': {
                            'meta': {
                                'count': 0
                            },
                            'data': []
                        },
                        'comments': {
                            'meta': {
                                'count': 0
                            },
                            'data': []
                        },
                        'commentsHyperlinked': {
                            'links': {
                                'self': 'http://testserver/entries/7/relationships/comments_hyperlinked',  # noqa: E501
                                'related': 'http://testserver/entries/7/comments'
                            }
                        },
                        'suggested': {
                            'links': {
                                'self': 'http://testserver/entries/7/relationships/suggested',
                                'related': 'http://testserver/entries/7/suggested/'
                            },
                            'data': [
                                {'type': 'entries', 'id': '1'},
                                {'type': 'entries', 'id': '2'},
                                {'type': 'entries', 'id': '3'},
                                {'type': 'entries', 'id': '4'},
                                {'type': 'entries', 'id': '5'},
                                {'type': 'entries', 'id': '6'},
                                {'type': 'entries', 'id': '8'},
                                {'type': 'entries', 'id': '9'},
                                {'type': 'entries', 'id': '10'},
                                {'type': 'entries', 'id': '11'},
                                {'type': 'entries', 'id': '12'}
                            ]
                        },
                        'suggestedHyperlinked': {
                            'links': {
                                'self': 'http://testserver/entries/7/relationships/suggested_hyperlinked',  # noqa: E501
                                'related': 'http://testserver/entries/7/suggested/'}
                        },
                        'tags': {
                            'data': []
                        },
                        'featuredHyperlinked': {
                            'links': {
                                'self': 'http://testserver/entries/7/relationships/featured_hyperlinked',  # noqa: E501
                                'related': 'http://testserver/entries/7/featured'
                            }
                        }
                    },
                    'meta': {
                        'bodyFormat': 'text'
                    }
                }
            ]
        }
        assert response.json() == expected_result

    def test_search_multiple_keywords(self):
        """
        test for `filter[search]=keyword1...` (keyword1 [AND keyword2...])

        See the four search_fields defined in views.py which demonstrate both searching
        direct fields (entry) and following ORM links to related fields (blog):
            `search_fields = ('headline', 'body_text', 'blog__name', 'blog__tagline')`

        SearchFilter searches for items that match all whitespace separated keywords across
        the many fields.

        This code tests that functionality by comparing the result of the GET request
        with the equivalent results used by filtering the test data via the model manager.
        To do so, iterate over the list of given searches:
        1. For each keyword, search the 4 search_fields for a match and then get the result
           set which is the union of all results for the given keyword.
        2. Intersect those results sets such that *all* keywords are represented.
        See `example/fixtures/blogentry.json` for the test content that the searches are based on.
        The searches test for both direct entries and related blogs across multiple fields.
        """
        for searches in ("research", "chemistry", "nonesuch",
                         "research seminar", "research nonesuch",
                         "barnard classic", "barnard ethnographic field research"):
            response = self.client.get(self.url, data={'filter[search]': searches})
            self.assertEqual(response.status_code, 200, msg=response.content.decode("utf-8"))
            dja_response = response.json()
            keys = searches.split()
            # dicts keyed by the search keys for the 4 search_fields:
            headline = {}      # list of entry ids where key is in entry__headline
            body_text = {}     # list of entry ids where key is in entry__body_text
            blog_name = {}     # list of entry ids where key is in entry__blog__name
            blog_tagline = {}  # list of entry ids where key is in entry__blog__tagline
            for key in keys:
                headline[key] = [str(k.id) for k in
                                 self.entries.filter(headline__icontains=key)]
                body_text[key] = [str(k.id) for k in
                                  self.entries.filter(body_text__icontains=key)]
                blog_name[key] = [str(k.id) for k in
                                  self.entries.filter(blog__name__icontains=key)]
                blog_tagline[key] = [str(k.id) for k in
                                     self.entries.filter(blog__tagline__icontains=key)]
            union = []  # each list item is a set of entry ids matching the given key
            for key in keys:
                union.append(set(headline[key] + body_text[key] +
                                 blog_name[key] + blog_tagline[key]))
            # all keywords must be present: intersect the keyword sets
            expected_ids = set.intersection(*union)
            expected_len = len(expected_ids)
            self.assertEqual(len(dja_response['data']), expected_len)
            returned_ids = set([k['id'] for k in dja_response['data']])
            self.assertEqual(returned_ids, expected_ids)

    def test_param_invalid(self):
        """
        Test a "wrong" query parameter
        """
        response = self.client.get(self.url, data={'garbage': 'foo'})
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "invalid query parameter: garbage")

    def test_param_duplicate(self):
        """
        Test a duplicated query parameter:
        `?sort=headline&page[size]=3&sort=bodyText` is not allowed.
        This is not so obvious when using a data dict....
        """
        response = self.client.get(self.url,
                                   data={'sort': ['headline', 'bodyText'],
                                         'page[size]': 3}
                                   )
        self.assertEqual(response.status_code, 400,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(dja_response['errors'][0]['detail'],
                         "repeated query parameter not allowed: sort")

    def test_many_params(self):
        """
        Test that filter params aren't ignored when many params are present
        """
        response = self.client.get(self.url,
                                   data={'filter[headline.regex]': '^A',
                                         'filter[body_text.regex]': '^IN',
                                         'filter[blog.name]': 'ANTB',
                                         'page[size]': 3})
        self.assertEqual(response.status_code, 200,
                         msg=response.content.decode("utf-8"))
        dja_response = response.json()
        self.assertEqual(len(dja_response['data']), 1)
        self.assertEqual(dja_response['data'][0]['id'], '1')
