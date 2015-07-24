import json

from example.tests import TestBase

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
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
        setattr(settings, 'JSON_API_FORMAT_KEYS', 'camelization')

    def tearDown(self):
        # Remove the format keys settings.
        setattr(settings, 'JSON_API_FORMAT_KEYS', 'dasherize')


    def test_camelization(self):
        """
        Test that camelization works.
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

        user = get_user_model().objects.all()[0]
        expected = {
            u'data': {
                u'type': u'users',
                u'id': user.pk,
                u'attributes': {
                    u'firstName': user.first_name,
                    u'lastName': user.last_name,
                    u'email': user.email
                },
            }
        }

        json_content = json.loads(response.content.decode('utf8'))
        links = json_content.get('links')

        self.assertEquals(expected.get('users'), json_content.get('users'))
        self.assertEqual(u'http://testserver/identities?page=2',
            links.get('next'))
