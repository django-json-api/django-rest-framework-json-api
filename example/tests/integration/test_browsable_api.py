import re

import pytest
from django.urls import reverse

from example.views import AuthorViewSet, EntryViewSet, ProjectTypeViewset

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def overwrite_filterbackends(monkeypatch):
    # TODO remove monkey patching when addressing issue #812
    monkeypatch.setattr(EntryViewSet, "filter_backends", [])
    monkeypatch.setattr(AuthorViewSet, "filter_backends", [])
    monkeypatch.setattr(ProjectTypeViewset, "filter_backends", [])


def test_browsable_api_with_included_serializers(single_entry, client):
    response = client.get(
        reverse("entry-detail", kwargs={"pk": single_entry.pk, "format": "api"})
    )
    content = str(response.content)
    assert response.status_code == 200
    assert re.search(r"JSON:API includes", content)
    assert re.search(
        r'<input type="checkbox" name="includes" [^>]* value="authors.bio"', content
    )


def test_browsable_api_on_related_url(author, client):
    url = reverse("author-related", kwargs={"pk": author.pk, "related_field": "bio"})
    response = client.get(url, data={"format": "api"})
    content = str(response.content)
    assert response.status_code == 200
    assert re.search(r"JSON:API includes", content)
    assert re.search(
        r'<input type="checkbox" name="includes" [^>]* value="metadata"', content
    )


def test_browsable_api_with_no_included_serializers(client):
    response = client.get(reverse("projecttype-list", kwargs={"format": "api"}))
    content = str(response.content)
    assert response.status_code == 200
    assert not re.search(r"JSON:API includes", content)
