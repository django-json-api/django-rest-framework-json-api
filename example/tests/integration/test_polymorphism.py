import pytest
from django.core.urlresolvers import reverse

from example.tests.utils import load_json

pytestmark = pytest.mark.django_db


def test_polymorphism_on_detail(single_art_project, client):
    response = client.get(reverse("project-detail", kwargs={'pk': single_art_project.pk}))
    content = load_json(response.content)
    assert content["data"]["type"] == "artProjects"


def test_polymorphism_on_detail_relations(single_company, client):
    response = client.get(reverse("company-detail", kwargs={'pk': single_company.pk}))
    content = load_json(response.content)
    assert content["data"]["relationships"]["currentProject"]["data"]["type"] == "artProjects"
    assert [rel["type"] for rel in content["data"]["relationships"]["futureProjects"]["data"]] == [
        "researchProjects", "artProjects"]


def test_polymorphism_on_included_relations(single_company, client):
    response = client.get(reverse("company-detail", kwargs={'pk': single_company.pk}) +
                          '?include=current_project,future_projects')
    content = load_json(response.content)
    assert content["data"]["relationships"]["currentProject"]["data"]["type"] == "artProjects"
    assert [rel["type"] for rel in content["data"]["relationships"]["futureProjects"]["data"]] == [
        "researchProjects", "artProjects"]
    assert [x.get('type') for x in content.get('included')] == ['artProjects', 'artProjects', 'researchProjects'], \
        'Detail included types are incorrect'
