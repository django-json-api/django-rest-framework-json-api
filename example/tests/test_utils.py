"""
Test rest_framework_json_api's utils functions.
"""
from django.http import QueryDict

from rest_framework_json_api import utils

import pytest

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

    def test_m2m_relation(self):
        """
        Ensure m2ms have their types identified correctly.
        """
        serializer = EntrySerializer()
        field = serializer.fields['authors']

        self.assertEqual(utils.get_related_resource_type(field), 'authors')


def test_format_query_params(settings):
    query_params = QueryDict(
        'filter[name]=Smith&filter[age]=50&other_random_param=10',
        mutable=True)

    new_params = utils.format_query_params(query_params)

    expected_params = QueryDict('name=Smith&age=50&other_random_param=10')

    for key, value in new_params.items():
        assert expected_params[key] == new_params[key]
