import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


# TODO: Need to have a view that includes the mixins.
def test_sort_view(multiple_entries, client):
    base_url = reverse('entry-list')
    querystring = '?sort=-blog,headlinexx'
    response = client.get(base_url + querystring)
    assert response.status_code == 200
