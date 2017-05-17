from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils import encoding

from example.tests import TestBase
from example.tests.utils import load_json


class FormatKeysSetTests(TestBase):
    """
    Test that camelization and underscoring of key names works if they are activated.
    """
    list_url = reverse('user-list')

    def setUp(self):
        super(FormatKeysSetTests, self).setUp()
        self.detail_url = reverse('user-detail', kwargs={'pk': self.miles.pk})

    def test_camelization(self):
        """
        Test that camelization works.
        """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

        user = get_user_model().objects.all()[0]
        expected = {
            'data': [
                {
                    'type': 'users',
                    'id': encoding.force_text(user.pk),
                    'attributes': {
                        'firstName': user.first_name,
                        'lastName': user.last_name,
                        'email': user.email
                    },
                }
            ],
            'links': {
                'first': 'http://testserver/identities?page=1',
                'last': 'http://testserver/identities?page=2',
                'next': 'http://testserver/identities?page=2',
                'prev': None
            },
            'meta': {
                'pagination': {
                    'page': 1,
                    'pages': 2,
                    'count': 2
                }
            }
        }

        parsed_content = load_json(response.content)

        assert expected == parsed_content
