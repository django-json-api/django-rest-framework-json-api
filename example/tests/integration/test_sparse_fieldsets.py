from django.core.urlresolvers import reverse

import pytest


pytestmark = pytest.mark.django_db


def test_sparse_fieldset_ordered_dict_error(multiple_entries, client):
    base_url = reverse('entry-list')
    querystring = '?fields[entries]=blog,headline'
    response = client.get(base_url + querystring)  # RuntimeError: OrderedDict mutated during iteration
    assert response.status_code == 200  # succeed if we didn't fail due to the above RuntimeError
