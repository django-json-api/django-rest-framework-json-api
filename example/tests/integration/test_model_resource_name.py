import pytest
from django.core.urlresolvers import reverse

from example.tests.utils import load_json

from rest_framework.test import APITestCase
from example import models, serializers
pytestmark = pytest.mark.django_db


def test_model_resource_name_on_list(single_entry, client):
    response = client.get(reverse("renamed-authors-list"))
    data = load_json(response.content)['data']
    # name should be super-author instead of model name RenamedAuthor
    assert [x.get('type') for x in data] == ['super-author'], 'List included types are incorrect'

@pytest.mark.usefixtures("single_entry")
class ResourceNameConsistencyTest(APITestCase):
    
    def test_type_match_on_included_and_inline_base(self):
        self._check_relationship_and_included_comment_type_are_the_same(reverse("entry-list"))

    def test_type_match_on_included_and_inline_with_JSONAPIMeta(self):
        models.Comment.__bases__ += (self._PatchedModel,)

        self._check_relationship_and_included_comment_type_are_the_same(reverse("entry-list"))

    def test_type_match_on_included_and_inline_with_serializer_resource_name(self):
        serializers.CommentSerializer.Meta.resource_name = "resource_name_from_serializer"

        self._check_relationship_and_included_comment_type_are_the_same(reverse("entry-list"))

    def test_type_match_on_included_and_inline_with_serializer_resource_name_and_JSONAPIMeta(self):
        models.Comment.__bases__ += (self._PatchedModel,)
        serializers.CommentSerializer.Meta.resource_name = "resource_name_from_serializer"

        self._check_relationship_and_included_comment_type_are_the_same(reverse("entry-list"))

    def test_resource_and_relationship_type_match(self):
        self._check_resource_and_relationship_comment_type_match()

    def test_resource_and_relationship_type_match_with_serializer_resource_name(self):
        serializers.CommentSerializer.Meta.resource_name = "resource_name_from_serializer"

        self._check_resource_and_relationship_comment_type_match()

    def test_resource_and_relationship_type_match_with_JSONAPIMeta(self):
        models.Comment.__bases__ += (self._PatchedModel,)

        self._check_resource_and_relationship_comment_type_match()

    def test_resource_and_relationship_type_match_with_serializer_resource_name_and_JSONAPIMeta(self):
        models.Comment.__bases__ += (self._PatchedModel,)
        serializers.CommentSerializer.Meta.resource_name = "resource_name_from_serializer"

        self._check_resource_and_relationship_comment_type_match()

    def _check_resource_and_relationship_comment_type_match(self):
        entry_response = self.client.get(reverse("entry-list"))
        comment_response = self.client.get(reverse("comment-list"))

        comment_resource_type = load_json(comment_response.content).get('data')[0].get('type')
        comment_relationship_type = load_json(entry_response.content).get(
            'data')[0].get('relationships').get('comments').get('data')[0].get('type')

        assert comment_resource_type == comment_relationship_type, "The resource type seen in the relationships and head resource do not match"

    def _check_relationship_and_included_comment_type_are_the_same(self, url):
        response = self.client.get(url + "?include=comments")
        data = load_json(response.content).get('data')[0]
        comment = load_json(response.content).get('included')[0]

        comment_relationship_type = data.get('relationships').get('comments').get('data')[0].get('type')
        comment_included_type = comment.get('type')

        assert comment_relationship_type == comment_included_type, "The resource type seen in the relationships and included do not match"

    def tearDown(self):
        models.Comment.__bases__ = (models.Comment.__bases__[0],)
        try:
            delattr(serializers.CommentSerializer.Meta, "resource_name")
        except AttributeError:
            pass

    class _PatchedModel:

        class JSONAPIMeta:
            resource_name = "resource_name_from_JSONAPIMeta"
            