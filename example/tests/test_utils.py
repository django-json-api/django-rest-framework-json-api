"""
Test rest_framework_json_api's utils functions.
"""
from rest_framework_json_api import utils

from example.serializers import AuthorSerializer, EntrySerializer
from example.tests import TestBase


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

    def test_m2m_relation(self):
        """
        Ensure m2ms have their types identified correctly.
        """
        serializer = EntrySerializer()
        field = serializer.fields['authors']

        self.assertEqual(utils.get_related_resource_type(field), 'authors')

    def test_m2m_reverse_relation(self):
        """
        Ensure reverse m2ms have their types identified correctly.
        """
        serializer = AuthorSerializer()
        field = serializer.fields['entries']

        self.assertEqual(utils.get_related_resource_type(field), 'entries')
