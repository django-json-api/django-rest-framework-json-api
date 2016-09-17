"""
Test rest_framework_json_api's utils functions.
"""
from rest_framework_json_api import utils

from ..serializers import EntrySerializer
from ..tests import TestBase


class GetRelatedResourceTests(TestBase):
    """
    Ensure the `get_related_resource_type` function returns correct types.
    """

    def test_reverse_relation(self):
        """
        Ensure reverse foreign keys have their types identified correctly.
        """
        serializer = EntrySerializer()
        field = serializer.fields['comments']

        self.assertEqual(utils.get_related_resource_type(field), 'comments')
