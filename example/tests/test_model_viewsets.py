import json

from example.tests import TestBase

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.conf import settings


class ModelViewSetTests(TestBase):
    """
    Test usage with ModelViewSets, also tests pluralization, camelization,
    and underscore.

    [<RegexURLPattern user-list ^identities/$>,
    <RegexURLPattern user-detail ^identities/(?P<pk>[^/]+)/$>]
    """
    list_url = reverse('user-list')

    def setUp(self):
        super(ModelViewSetTests, self).setUp()
        self.detail_url = reverse('user-detail', kwargs={'pk': self.miles.pk})

    def test_key_in_list_result(self):
        """
        Ensure the result has a 'user' key since that is the name of the model
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

        user = get_user_model().objects.all()[0]
        expected = {
            u'user': [{
                u'id': user.pk,
                u'first_name': user.first_name,
                u'last_name': user.last_name,
                u'email': user.email
            }]
        }

        json_content = json.loads(response.content.decode('utf8'))
        meta = json_content.get('meta')

        self.assertEquals(expected.get('user'), json_content.get('user'))
        self.assertEquals(meta.get('total'), 2)
        self.assertEquals(meta.get('count', 0),
            get_user_model().objects.count())
        self.assertEquals(meta.get('next'), 2)
        self.assertEqual(u'http://testserver/identities?page=2',
            meta.get('next_link'))
        self.assertEqual(meta.get('page'), 1)

    def test_page_two_in_list_result(self):
        """
        Ensure that the second page is reachable and is the correct data.
        """
        response = self.client.get(self.list_url, {'page': 2})
        self.assertEqual(response.status_code, 200)

        user = get_user_model().objects.all()[1]
        expected = {
            u'user': [{
                u'id': user.pk,
                u'first_name': user.first_name,
                u'last_name': user.last_name,
                u'email': user.email
            }]
        }

        json_content = json.loads(response.content.decode('utf8'))
        meta = json_content.get('meta')

        self.assertEquals(expected.get('user'), json_content.get('user'))
        self.assertEquals(meta.get('count', 0),
            get_user_model().objects.count())
        self.assertIsNone(meta.get('next'))
        self.assertIsNone(meta.get('next_link'))
        self.assertEqual(meta.get('previous'), 1)
        self.assertEqual(meta.get('page'), 2)

        # Older versions of DRF add page=1 for first page. Later trim to root
        try:
            self.assertEqual(u'http://testserver/identities',
                meta.get('previous_link'))
        except AssertionError:
            self.assertEqual(u'http://testserver/identities?page=1',
                meta.get('previous_link'))

    def test_page_range_in_list_result(self):
        """
        Ensure that the range of a page can be changed from the client,
        tests pluralization as two objects means it converts ``user`` to
        ``users``.
        """
        response = self.client.get(self.list_url, {'page_size': 2})
        self.assertEqual(response.status_code, 200)

        users = get_user_model().objects.all()
        expected = {
            u'users': [{
                u'id': users[0].pk,
                u'first_name': users[0].first_name,
                u'last_name': users[0].last_name,
                u'email': users[0].email
            },{
                u'id': users[1].pk,
                u'first_name': users[1].first_name,
                u'last_name': users[1].last_name,
                u'email': users[1].email
            }]
        }

        json_content = json.loads(response.content.decode('utf8'))
        meta = json_content.get('meta')
        self.assertEquals(expected.get('users'), json_content.get('user'))
        self.assertEquals(meta.get('count', 0),
            get_user_model().objects.count())


    def test_key_in_detail_result(self):
        """
        Ensure the result has a 'user' key.
        """
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.content.decode('utf8'))
        expected = {
            u'user': {
                u'id': self.miles.pk,
                u'first_name': self.miles.first_name,
                u'last_name': self.miles.last_name,
                u'email': self.miles.email
            }
        }
        self.assertEqual(result, expected)

    def test_key_in_post(self):
        """
        Ensure a key is in the post.
        """
        self.client.login(username='miles', password='pw')
        data = {
            u'user': {
                u'id': self.miles.pk,
                u'first_name': self.miles.first_name,
                u'last_name': self.miles.last_name,
                u'email': 'miles@trumpet.org'
            }
        }
        response = self.client.put(self.detail_url, data=data, format='json')

        result = json.loads(response.content.decode('utf8'))

        self.assertIn('user', result.keys())
        self.assertEqual(result['user']['email'], 'miles@trumpet.org')

        # is it updated?
        self.assertEqual(
            get_user_model().objects.get(pk=self.miles.pk).email,
            'miles@trumpet.org')

