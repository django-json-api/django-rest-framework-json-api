import pytest
from django.urls import reverse
from rest_framework import status

from example.views import EntryViewSet

pytestmark = pytest.mark.django_db


def test_sparse_fieldset_valid_fields(client, entry):
    base_url = reverse("entry-list")
    response = client.get(base_url, data={"fields[entries]": "blog,headline"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]

    assert len(data) == 1
    entry = data[0]
    assert entry["attributes"].keys() == {"headline"}
    assert entry["relationships"].keys() == {"blog"}
    assert "meta" not in entry


@pytest.mark.parametrize(
    "fields_param", ["invalidfields[entries]", "fieldsinvalid[entries"]
)
def test_sparse_fieldset_invalid_fields_parameter(
    client, entry, fields_param, monkeypatch
):
    """
    Test that invalid fields query parameter is not processed by sparse fieldset.

    rest_framework_json_api.filters.QueryParameterValidationFilter takes care of error
    handling in such a case.
    """
    # disable QueryParameterValidationFilter
    monkeypatch.setattr(EntryViewSet, "filter_backends", [])

    base_url = reverse("entry-list")
    response = client.get(base_url, data={fields_param: "blog,headline"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]

    assert len(data) == 1
    entry = data[0]
    assert entry["attributes"].keys() != {"headline"}
    assert entry["relationships"].keys() != {"blog"}
