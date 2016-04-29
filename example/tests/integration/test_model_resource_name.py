import pytest
from django.core.urlresolvers import reverse

from example.tests.utils import load_json

from example import models, serializers, views
pytestmark = pytest.mark.django_db


class _PatchedModel:
    class JSONAPIMeta:
        resource_name = "resource_name_from_JSONAPIMeta"


def _check_resource_and_relationship_comment_type_match(django_client):
    entry_response = django_client.get(reverse("entry-list"))
    comment_response = django_client.get(reverse("comment-list"))

    comment_resource_type = load_json(comment_response.content).get('data')[0].get('type')
    comment_relationship_type = load_json(entry_response.content).get(
        'data')[0].get('relationships').get('comments').get('data')[0].get('type')

    assert comment_resource_type == comment_relationship_type, "The resource type seen in the relationships and head resource do not match"


def _check_relationship_and_included_comment_type_are_the_same(django_client, url):
    response = django_client.get(url + "?include=comments")
    data = load_json(response.content).get('data')[0]
    comment = load_json(response.content).get('included')[0]

    comment_relationship_type = data.get('relationships').get('comments').get('data')[0].get('type')
    comment_included_type = comment.get('type')

    assert comment_relationship_type == comment_included_type, "The resource type seen in the relationships and included do not match"


@pytest.mark.usefixtures("single_entry")
class TestModelResourceName:

    def test_model_resource_name_on_list(self, client):
        models.Comment.__bases__ += (_PatchedModel,)
        response = client.get(reverse("comment-list"))
        data = load_json(response.content)['data'][0]
        # name should be super-author instead of model name RenamedAuthor
        assert (data.get('type') == 'resource_name_from_JSONAPIMeta'), (
            'resource_name from model incorrect on list')

    # Precedence tests
    def test_resource_name_precendence(self, client):
        # default
        response = client.get(reverse("comment-list"))
        data = load_json(response.content)['data'][0]
        assert (data.get('type') == 'comments'), (
            'resource_name from model incorrect on list')

        # model > default
        models.Comment.__bases__ += (_PatchedModel,)
        response = client.get(reverse("comment-list"))
        data = load_json(response.content)['data'][0]
        assert (data.get('type') == 'resource_name_from_JSONAPIMeta'), (
            'resource_name from model incorrect on list')

        # serializer > model
        serializers.CommentSerializer.Meta.resource_name = "resource_name_from_serializer"
        response = client.get(reverse("comment-list"))
        data = load_json(response.content)['data'][0]
        assert (data.get('type') == 'resource_name_from_serializer'), (
            'resource_name from serializer incorrect on list')

        # view > serializer > model
        views.CommentViewSet.resource_name = 'resource_name_from_view'
        response = client.get(reverse("comment-list"))
        data = load_json(response.content)['data'][0]
        assert (data.get('type') == 'resource_name_from_view'), (
            'resource_name from view incorrect on list')

    def teardown_method(self, method):
        models.Comment.__bases__ = (models.Comment.__bases__[0],)
        try:
            delattr(serializers.CommentSerializer.Meta, "resource_name")
        except AttributeError:
            pass
        try:
            delattr(views.CommentViewSet, "resource_name")
        except AttributeError:
            pass


@pytest.mark.usefixtures("single_entry")
class TestResourceNameConsistency:

    # Included rename tests
    def test_type_match_on_included_and_inline_base(self, client):
        _check_relationship_and_included_comment_type_are_the_same(client, reverse("entry-list"))

    def test_type_match_on_included_and_inline_with_JSONAPIMeta(self, client):
        models.Comment.__bases__ += (_PatchedModel,)

        _check_relationship_and_included_comment_type_are_the_same(client, reverse("entry-list"))

    def test_type_match_on_included_and_inline_with_serializer_resource_name(self, client):
        serializers.CommentSerializer.Meta.resource_name = "resource_name_from_serializer"

        _check_relationship_and_included_comment_type_are_the_same(client, reverse("entry-list"))

    def test_type_match_on_included_and_inline_without_serializer_resource_name(self, client):
        serializers.CommentSerializer.Meta.resource_name = None

        _check_relationship_and_included_comment_type_are_the_same(client, reverse("entry-list"))

    def test_type_match_on_included_and_inline_with_serializer_resource_name_and_JSONAPIMeta(self, client):
        models.Comment.__bases__ += (_PatchedModel,)
        serializers.CommentSerializer.Meta.resource_name = "resource_name_from_serializer"

        _check_relationship_and_included_comment_type_are_the_same(client, reverse("entry-list"))

    # Relation rename tests
    def test_resource_and_relationship_type_match(self, client):
        _check_resource_and_relationship_comment_type_match(client)

    def test_resource_and_relationship_type_match_with_serializer_resource_name(self, client):
        serializers.CommentSerializer.Meta.resource_name = "resource_name_from_serializer"

        _check_resource_and_relationship_comment_type_match(client)

    def test_resource_and_relationship_type_match_with_JSONAPIMeta(self, client):
        models.Comment.__bases__ += (_PatchedModel,)

        _check_resource_and_relationship_comment_type_match(client)

    def test_resource_and_relationship_type_match_with_serializer_resource_name_and_JSONAPIMeta(self, client):
        models.Comment.__bases__ += (_PatchedModel,)
        serializers.CommentSerializer.Meta.resource_name = "resource_name_from_serializer"

        _check_resource_and_relationship_comment_type_match(client)

    def teardown_method(self, method):
        models.Comment.__bases__ = (models.Comment.__bases__[0],)
        try:
            delattr(serializers.CommentSerializer.Meta, "resource_name")
        except AttributeError:
            pass
