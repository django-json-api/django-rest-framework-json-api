import pytest
from django.core.urlresolvers import reverse

from example.tests.utils import load_json

pytestmark = pytest.mark.django_db


def test_model_resource_name_on_list(single_entry, client):
    response = client.get(reverse("renamed-authors-list"))
    data = load_json(response.content)['data']
    # name should be super-author instead of model name RenamedAuthor
    assert [x.get('type') for x in data] == ['super-author'], 'List included types are incorrect'
