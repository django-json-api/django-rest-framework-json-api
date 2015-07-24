import json
from example.tests import TestBase
from django.core.urlresolvers import reverse
from django.conf import settings
from rest_framework.serializers import ValidationError


class GenericValidationTest(TestBase):
    """
    Test that a non serializer specific validation can be thrown and formatted
    """
    def setUp(self):
        super(GenericValidationTest, self).setUp()
        self.url = reverse('user-validation', kwargs={'pk': self.miles.pk})

    def test_generic_validation_error(self):
        """
        Check error formatting
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)

        result = json.loads(response.content.decode('utf8'))
        expected = {
            'errors': [{
                'status': '400',
                'source': {
                    'pointer': '/data'
                },
                'detail': 'Oh nohs!'
            }]
        }
        self.assertEqual(result, expected)
