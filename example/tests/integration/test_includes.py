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

