import pytest
from django.core.urlresolvers import reverse

from example.tests.utils import load_json

pytestmark = pytest.mark.django_db


def test_included_data_on_list(multiple_entries, client):
    response = client.get(reverse("entry-list") + '?include=comments')
    included = load_json(response.content).get('included')

    assert len(load_json(response.content)['data']) == len(multiple_entries)
    assert [x.get('type') for x in included] == ['comments']
    assert (len([resource for resource in included if resource["type"] == "comments"]) ==
            sum([entry.comment_set.count() for entry in multiple_entries]))


def test_included_data_on_detail(single_entry, client):
    response = client.get(reverse("entry-detail", kwargs={'pk': single_entry.pk}) + '?include=comments')
    included = load_json(response.content).get('included')

    assert [x.get('type') for x in included] == ['comments']
    assert (len([resource for resource in included if resource["type"] == "comments"]) ==
            single_entry.comment_set.count())
