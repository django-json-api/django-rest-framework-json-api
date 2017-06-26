from django.conf import settings
from django.core.urlresolvers import reverse

from example.tests import TestBase
from example.tests.utils import load_json


class GenericViewSet(TestBase):
    """
    Test expected responses coming from a Generic ViewSet
    """

    def setUp(self):
        super(GenericViewSet, self).setUp()

        setattr(settings, 'JSON_API_FORMAT_KEYS', 'dasherize')

    def tearDown(self):

        setattr(settings, 'JSON_API_FORMAT_KEYS', 'camelize')

    def test_default_rest_framework_behavior(self):
        """
        This is more of an example really, showing default behavior
        """
        url = reverse('user-default', kwargs={'pk': self.miles.pk})

        response = self.client.get(url)

        self.assertEqual(200, response.status_code)

        expected = {
            'id': 2,
            'first_name': 'Miles',
            'last_name': 'Davis',
            'email': 'miles@example.com'
        }

        parsed_content = load_json(response.content)

        assert expected == parsed_content

    def test_ember_expected_renderer(self):
        """
        The :class:`UserEmber` ViewSet has the ``resource_name`` of 'data'
        so that should be the key in the JSON response.
        """
        url = reverse('user-manual-resource-name', kwargs={'pk': self.miles.pk})

        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

        expected = {
            'data': {
                'type': 'data',
                'id': '2',
                'attributes': {
                    'first-name': 'Miles',
                    'last-name': 'Davis',
                    'email': 'miles@example.com'
                }
            }
        }

        parsed_content = load_json(response.content)

        assert expected == parsed_content

    def test_default_validation_exceptions(self):
        """
        Default validation exceptions should conform to json api spec
        """
        expected = {
            'errors': [
                {
                    'status': '400',
                    'source': {
                        'pointer': '/data/attributes/email',
                    },
                    'detail': 'Enter a valid email address.',
                },
                {
                    'status': '400',
                    'source': {
                        'pointer': '/data/attributes/first-name',
                    },
                    'detail': 'There\'s a problem with first name',
                }
            ]
        }
        response = self.client.post('/identities', {
            'email': 'bar', 'first_name': 'alajflajaljalajlfjafljalj'})

        parsed_content = load_json(response.content)

        assert expected == parsed_content

    def test_custom_validation_exceptions(self):
        """
        Exceptions should be able to be formatted manually
        """
        expected = {
            'errors': [
                {
                    'id': 'armageddon101',
                    'detail': 'Hey! You need a last name!',
                    'meta': 'something',
                },
                {
                    'status': '400',
                    'source': {
                        'pointer': '/data/attributes/email',
                    },
                    'detail': 'Enter a valid email address.',
                },
            ]
        }
        response = self.client.post('/identities', {
            'email': 'bar', 'last_name': 'alajflajaljalajlfjafljalj'})

        parsed_content = load_json(response.content)

        assert expected == parsed_content
