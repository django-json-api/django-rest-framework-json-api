import json

from example.tests import TestBase

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse, reverse
from django.conf import settings


class FormatKeysSetTests(TestBase):
    """
    Test that camelization and underscoring of key names works if they are activated.
    """
    list_url = reverse('user-list')

    def setUp(self):
        super(FormatKeysSetTests, self).setUp()
        self.detail_url = reverse('user-detail', kwargs={'pk': self.miles.pk})

        # Set the format keys settings.
        setattr(settings, 'REST_EMBER_FORMAT_KEYS', True)
        setattr(settings, 'REST_EMBER_PLURALIZE_KEYS', True)

    def tearDown(self):
        # Remove the format keys settings.
        delattr(settings, 'REST_EMBER_FORMAT_KEYS')
        delattr(settings, 'REST_EMBER_PLURALIZE_KEYS')


    def test_camelization(self):
        """
        Test that camelization works.
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

        user = get_user_model().objects.all()[0]
        expected = {
            u'users': [{
                u'id': user.pk,
                u'firstName': user.first_name,
                u'lastName': user.last_name,
                u'email': user.email
            }]
        }

        json_content = json.loads(response.content.decode('utf8'))
        meta = json_content.get('meta')

        self.assertEquals(expected.get('users'), json_content.get('users'))
        self.assertEqual(u'http://testserver/identities?page=2',
            meta.get('nextLink'))

    def test_pluralization(self):
        """
        Test that the key name is pluralized.
        """
        response = self.client.get(self.list_url, {'page_size': 2})
        self.assertEqual(response.status_code, 200)

        users = get_user_model().objects.all()
        expected = {
            u'users': [{
                u'id': users[0].pk,
                u'firstName': users[0].first_name,
                u'lastName': users[0].last_name,
                u'email': users[0].email
            },{
                u'id': users[1].pk,
                u'firstName': users[1].first_name,
                u'lastName': users[1].last_name,
                u'email': users[1].email
            }]
        }

        json_content = json.loads(response.content.decode('utf8'))
        self.assertEquals(expected.get('users'), json_content.get('users'))

    def test_empty_pluralization(self):
        #test that the key is still pluralized when there are no records for the
        #model, as long as the endpoint serves a list
        response = self.client.get(reverse('user-empty-list'))
        self.assertEqual(response.status_code, 200)

        json_content = json.loads(response.content.decode('utf8'))
        self.assertEqual(json_content.get('users'), [])

