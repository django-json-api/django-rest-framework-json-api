from copy import deepcopy

import pytest
from django.urls import reverse
from rest_framework import status

from example import models, serializers, views

pytestmark = pytest.mark.django_db


class _PatchedModel:
    class JSONAPIMeta:
        resource_name = "resource_name_from_JSONAPIMeta"


def _check_resource_and_relationship_comment_type_match(django_client):
    entry_response = django_client.get(reverse("entry-list"))
    comment_response = django_client.get(reverse("comment-list"))

    comment_resource_type = comment_response.json().get('data')[0].get('type')
    comment_relationship_type = entry_response.json().get(
        'data')[0].get('relationships').get('comments').get('data')[0].get('type')

    assert comment_resource_type == comment_relationship_type, (
        "The resource type seen in the relationships and head resource do not match"
    )


def _check_relationship_and_included_comment_type_are_the_same(django_client, url):
    response = django_client.get(url + "?include=comments")
    data = response.json().get('data')[0]
    comment = response.json().get('included')[0]

    comment_relationship_type = data.get('relationships').get('comments').get('data')[0].get('type')
    comment_included_type = comment.get('type')

    assert comment_relationship_type == comment_included_type, (
        "The resource type seen in the relationships and included do not match"
    )


@pytest.mark.usefixtures("single_entry")
class TestModelResourceName:

    create_data = {
        'data': {
            'type': 'resource_name_from_JSONAPIMeta',
            'id': None,
            'attributes': {
                'body': 'example',
            },
            'relationships': {
                'entry': {
                    'data': {
                        'type': 'resource_name_from_JSONAPIMeta',
                        'id': 1
                    }
                }
            }
        }
    }

    def test_model_resource_name_on_list(self, client):
        models.Comment.__bases__ += (_PatchedModel,)
        response = client.get(reverse("comment-list"))
        data = response.json()['data'][0]
        # name should be super-author instead of model name RenamedAuthor
        assert (data.get('type') == 'resource_name_from_JSONAPIMeta'), (
            'resource_name from model incorrect on list')

    # Precedence tests
    def test_resource_name_precendence(self, client, monkeypatch):
        # default
        response = client.get(reverse("comment-list"))
        data = response.json()['data'][0]
        assert (data.get('type') == 'comments'), (
            'resource_name from model incorrect on list')

        # model > default
        models.Comment.__bases__ += (_PatchedModel,)
        response = client.get(reverse("comment-list"))
        data = response.json()['data'][0]
        assert (data.get('type') == 'resource_name_from_JSONAPIMeta'), (
            'resource_name from model incorrect on list')

        # serializer > model
        monkeypatch.setattr(
            serializers.CommentSerializer.Meta,
            'resource_name',
            'resource_name_from_serializer',
            False
        )
        response = client.get(reverse("comment-list"))
        data = response.json()['data'][0]
        assert (data.get('type') == 'resource_name_from_serializer'), (
            'resource_name from serializer incorrect on list')

        # view > serializer > model
        monkeypatch.setattr(views.CommentViewSet, 'resource_name', 'resource_name_from_view', False)
        response = client.get(reverse("comment-list"))
        data = response.json()['data'][0]
        assert (data.get('type') == 'resource_name_from_view'), (
            'resource_name from view incorrect on list')

    def test_model_resource_name_create(self, client):
        models.Comment.__bases__ += (_PatchedModel,)
        models.Entry.__bases__ += (_PatchedModel,)
        response = client.post(reverse("comment-list"), self.create_data)

        assert response.status_code == status.HTTP_201_CREATED

    def test_serializer_resource_name_create(self, client, monkeypatch):
        monkeypatch.setattr(
            serializers.CommentSerializer.Meta,
            'resource_name',
            'renamed_comments',
            False
        )
        monkeypatch.setattr(
            serializers.EntrySerializer.Meta,
            'resource_name',
            'renamed_entries',
            False
        )
        create_data = deepcopy(self.create_data)
        create_data['data']['type'] = 'renamed_comments'
        create_data['data']['relationships']['entry']['data']['type'] = 'renamed_entries'

        response = client.post(reverse("comment-list"), create_data)

        assert response.status_code == status.HTTP_201_CREATED

    def teardown_method(self, method):
        models.Comment.__bases__ = (models.Comment.__bases__[0],)
        models.Entry.__bases__ = (models.Entry.__bases__[0],)


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

    def test_type_match_on_included_and_inline_with_serializer_resource_name_and_JSONAPIMeta(
            self, client
    ):
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

    def test_resource_and_relationship_type_match_with_serializer_resource_name_and_JSONAPIMeta(
            self, client
    ):
        models.Comment.__bases__ += (_PatchedModel,)
        serializers.CommentSerializer.Meta.resource_name = "resource_name_from_serializer"

        _check_resource_and_relationship_comment_type_match(client)

    def teardown_method(self, method):
        models.Comment.__bases__ = (models.Comment.__bases__[0],)
        try:
            delattr(serializers.CommentSerializer.Meta, "resource_name")
        except AttributeError:
            pass
