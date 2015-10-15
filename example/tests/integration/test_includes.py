import pytest, json
from django.core.urlresolvers import reverse

pytestmark = pytest.mark.django_db


def test_included_data_on_list(single_entry, client):
    response = client.get(reverse("entry-list") + '?include=comments')
    included = json.loads(response.content).get('included')

    assert [x.get('type') for x in included] == ['comments']

def test_included_data_on_detail(single_entry, client):
    response = client.get(reverse("entry-detail", kwargs={'pk': single_entry.pk}) + '?include=comments')
    included = json.loads(response.content).get('included')

    assert [x.get('type') for x in included] == ['comments']

