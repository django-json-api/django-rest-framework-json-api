import pytest
from django.core.urlresolvers import reverse

from example.tests.utils import load_json
import mock

pytestmark = pytest.mark.django_db



@mock.patch('rest_framework_json_api.utils.get_default_included_resources_from_serializer', new=lambda s: ['comments'])
def test_default_included_data_on_list(multiple_entries, client):
    return test_included_data_on_list(multiple_entries=multiple_entries, client=client, query='?page_size=5')


def test_included_data_on_list(multiple_entries, client, query='?include=comments&page_size=5'):
    response = client.get(reverse("entry-list") + query)
    included = load_json(response.content).get('included')

    assert len(load_json(response.content)['data']) == len(multiple_entries), 'Incorrect entry count'
    assert [x.get('type') for x in included] == ['comments', 'comments'], 'List included types are incorrect'

    comment_count = len([resource for resource in included if resource["type"] == "comments"])
    expected_comment_count = sum([entry.comment_set.count() for entry in multiple_entries])
    assert comment_count == expected_comment_count, 'List comment count is incorrect'


@mock.patch('rest_framework_json_api.utils.get_default_included_resources_from_serializer', new=lambda s: ['comments'])
def test_default_included_data_on_detail(single_entry, client):
    return test_included_data_on_detail(single_entry=single_entry, client=client, query='')


def test_included_data_on_detail(single_entry, client, query='?include=comments'):
    response = client.get(reverse("entry-detail", kwargs={'pk': single_entry.pk}) + query)
    included = load_json(response.content).get('included')

    assert [x.get('type') for x in included] == ['comments'], 'Detail included types are incorrect'

    comment_count = len([resource for resource in included if resource["type"] == "comments"])
    expected_comment_count = single_entry.comment_set.count()
    assert comment_count == expected_comment_count, 'Detail comment count is incorrect'


def test_dynamic_related_data_is_included(single_entry, entry_factory, client):
    entry_factory()
    response = client.get(reverse("entry-detail", kwargs={'pk': single_entry.pk}) + '?include=featured')
    included = load_json(response.content).get('included')

    assert [x.get('type') for x in included] == ['entries'], 'Dynamic included types are incorrect'
    assert len(included) == 1, 'The dynamically included blog entries are of an incorrect count'


def test_missing_field_not_included(author_bio_factory, author_factory, client):
    # First author does not have a bio
    author = author_factory(bio=None)
    response = client.get(reverse('author-detail', args=[author.pk])+'?include=bio')
    data = load_json(response.content)
    assert 'included' not in data
    # Second author does
    author = author_factory()
    response = client.get(reverse('author-detail', args=[author.pk])+'?include=bio')
    data = load_json(response.content)
    assert 'included' in data
    assert len(data['included']) == 1
    assert data['included'][0]['attributes']['body'] == author.bio.body


def test_deep_included_data_on_list(multiple_entries, client):
    response = client.get(reverse("entry-list") + '?include=comments,comments.author,'
                          'comments.author.bio&page_size=5')
    included = load_json(response.content).get('included')

    assert len(load_json(response.content)['data']) == len(multiple_entries), 'Incorrect entry count'
    assert [x.get('type') for x in included] == [
        'authorBios', 'authorBios', 'authors', 'authors', 'comments', 'comments'
    ], 'List included types are incorrect'

    comment_count = len([resource for resource in included if resource["type"] == "comments"])
    expected_comment_count = sum([entry.comment_set.count() for entry in multiple_entries])
    assert comment_count == expected_comment_count, 'List comment count is incorrect'

    author_count = len([resource for resource in included if resource["type"] == "authors"])
    expected_author_count = sum(
        [entry.comment_set.filter(author__isnull=False).count() for entry in multiple_entries])
    assert author_count == expected_author_count, 'List author count is incorrect'

    author_bio_count = len([resource for resource in included if resource["type"] == "authorBios"])
    expected_author_bio_count = sum([entry.comment_set.filter(
        author__bio__isnull=False).count() for entry in multiple_entries])
    assert author_bio_count == expected_author_bio_count, 'List author bio count is incorrect'

    # Also include entry authors
    response = client.get(reverse("entry-list") + '?include=authors,comments,comments.author,'
                          'comments.author.bio&page_size=5')
    included = load_json(response.content).get('included')

    assert len(load_json(response.content)['data']) == len(multiple_entries), 'Incorrect entry count'
    assert [x.get('type') for x in included] == [
        'authorBios', 'authorBios', 'authors', 'authors', 'authors', 'authors',
        'comments', 'comments'], 'List included types are incorrect'

    author_count = len([resource for resource in included if resource["type"] == "authors"])
    expected_author_count = sum(
        [entry.authors.count() for entry in multiple_entries] +
        [entry.comment_set.filter(author__isnull=False).count() for entry in multiple_entries])
    assert author_count == expected_author_count, 'List author count is incorrect'


def test_deep_included_data_on_detail(single_entry, client):
    # Same test as in list but also ensures that intermediate resources (here comments' authors)
    # are returned along with the leaf nodes
    response = client.get(reverse("entry-detail", kwargs={'pk': single_entry.pk}) +
                          '?include=comments,comments.author.bio')
    included = load_json(response.content).get('included')

    assert [x.get('type') for x in included] == ['authorBios', 'authors', 'comments'], \
        'Detail included types are incorrect'

    comment_count = len([resource for resource in included if resource["type"] == "comments"])
    expected_comment_count = single_entry.comment_set.count()
    assert comment_count == expected_comment_count, 'Detail comment count is incorrect'

    author_bio_count = len([resource for resource in included if resource["type"] == "authorBios"])
    expected_author_bio_count = single_entry.comment_set.filter(author__bio__isnull=False).count()
    assert author_bio_count == expected_author_bio_count, 'Detail author bio count is incorrect'
