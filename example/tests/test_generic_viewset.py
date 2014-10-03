
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
            json.loads(response.content),
            {
                'id': self.miles.pk,
                'first_name': self.miles.first_name,
                'last_name': self.miles.last_name,
                'email': self.miles.email
            }
        )

    def test_ember_expected_renderer(self):
        """
        The :class:`UserEmber` ViewSet has the ``resource_name`` of 'data'
        so that should be the key in the JSON response.
        """
        url = reverse('user-ember', kwargs={'pk': self.miles.pk})

        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            json.loads(response.content),
            {
                'data': {
                    'id': self.miles.pk,
                    'first_name': self.miles.first_name,
                    'last_name': self.miles.last_name,
                    'email': self.miles.email
                }
            }
        )

