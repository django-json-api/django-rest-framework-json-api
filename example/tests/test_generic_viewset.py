import json
from example.tests import TestBase
from django.core.urlresolvers import reverse
from django.conf import settings


class GenericViewSet(TestBase):
    """
    Test expected responses coming from a Generic ViewSet
    """
    def test_default_rest_framework_behavior(self):
        """
        This is more of an example really, showing default behavior
        """
        url = reverse('user-default', kwargs={'pk': self.miles.pk})

        response = self.client.get(url)

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            {
                'id': 2,
                'first_name': u'Miles',
                'last_name': u'Davis',
                'email': u'miles@example.com'
            }
        )

    def test_ember_expected_renderer(self):
        """
        The :class:`UserEmber` ViewSet has the ``resource_name`` of 'data'
        so that should be the key in the JSON response.
        """
        url = reverse('user-manual-resource-name', kwargs={'pk': self.miles.pk})

        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            {
                'data': {
                    'id': 2,
                    'first_name': u'Miles',
                    'last_name': u'Davis',
                    'email': u'miles@example.com'
                }
            }
        )

    def test_custom_exceptions(self):
        """
        Exceptions should conform to json api spec
        """
        response = self.client.post('/identities', {
            'email': 'bar', 'first_name': 'alajflajaljalajlfjafljalj'})
        self.assertEqual(
            json.loads(response.content.decode('utf8')),
            {
                'errors': [
                    {
                        'source': {
                            'parameter': 'email'
                        },
                        'detail': 'Enter a valid email address.'
                    },
                    {
                        'source': {
                            'parameter': 'first_name'
                        },
                        'detail': 'There\'s a problem with first name'
                    },
                ]
            }
        )


