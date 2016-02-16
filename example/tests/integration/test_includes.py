import pytest
from django.core.urlresolvers import reverse

from example.tests.utils import load_json

pytestmark = pytest.mark.django_db


def test_included_data_on_list(multiple_entries, client):
    response = client.get(reverse("entry-list") + '?include=comments&page_size=5')
    included = load_json(response.content).get('included')

    assert len(load_json(response.content)['data']) == len(multiple_entries), 'Incorrect entry count'
    assert [x.get('type') for x in included] == ['comments', 'comments'], 'List included types are incorrect'

    comment_count = len([resource for resource in included if resource["type"] == "comments"])
    expected_comment_count = sum([entry.comment_set.count() for entry in multiple_entries])
    assert comment_count == expected_comment_count, 'List comment count is incorrect'


def test_included_data_on_detail(single_entry, client):
    response = client.get(reverse("entry-detail", kwargs={'pk': single_entry.pk}) + '?include=comments')
    included = load_json(response.content).get('included')

    assert [x.get('type') for x in included] == ['comments'], 'Detail included types are incorrect'

    comment_count = len([resource for resource in included if resource["type"] == "comments"])
    expected_comment_count = single_entry.comment_set.count()
    assert comment_count == expected_comment_count, 'Detail comment count is incorrect'

def test_dynamic_related_data_is_included(single_entry, entry_factory, client):
    entry_factory()
    response = client.get(reverse("entry-detail", kwargs={'pk': single_entry.pk}) + '?include=suggested')
    included = load_json(response.content).get('included')

    assert [x.get('type') for x in included] == ['entries'], 'Dynamic included types are incorrect'
    assert len(included) == 1, 'The dynamically included blog entries are of an incorrect count'


def test_missing_field_not_included(author_bio_factory, author_factory, client):
    # First author does not have a bio
    author = author_factory()
    response = client.get(reverse('author-detail', args=[author.pk])+'?include=bio')
    data = load_json(response.content)
    assert 'included' not in data
    # Second author does
    bio = author_bio_factory()
    response = client.get(reverse('author-detail', args=[bio.author.pk])+'?include=bio')
    data = load_json(response.content)
    assert 'included' in data
    assert len(data['included']) == 1
    assert data['included'][0]['attributes']['body'] == bio.body

def test_reverse_included(single_entry, client):
    """Test the parsing of included names"""
    from django.conf import settings

    parse_relation       = getattr(settings, 'JSON_API_PARSE_RELATION_KEYS', None)
    singularize_included = getattr(settings, 'JSON_API_SINGULARIZE_INCLUDE_TYPE', None)

    settings.JSON_API_PARSE_RELATION_KEYS = 'underscore'
    settings.JSON_API_SINGULARIZE_INCLUDE_TYPE = True

    response = client.get(reverse('entry-list') + '?include=blogs')
    included = load_json(response.content).get('included')

    assert [x.get('type') for x in included] == ['blogs'], 'Related Blogs are incorrect'

    settings.JSON_API_PARSE_RELATION_KEYS      = parse_relation
    settings.JSON_API_SINGULARIZE_INCLUDE_TYPE = singularize_included
