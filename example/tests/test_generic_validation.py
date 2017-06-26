from django.core.urlresolvers import reverse

from example.tests import TestBase
from example.tests.utils import load_json


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

        expected = {
            'errors': [{
                'status': '400',
                'source': {
                    'pointer': '/data'
                },
                'detail': 'Oh nohs!'
            }]
        }

        parsed_content = load_json(response.content)

        assert expected == parsed_content
