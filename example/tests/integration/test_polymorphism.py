import random

import pytest
from django.urls import reverse
from rest_framework import status

from example.factories import ArtProjectFactory, ProjectTypeFactory

pytestmark = pytest.mark.django_db


def test_polymorphism_on_detail(single_art_project, client):
    response = client.get(
        reverse("project-detail", kwargs={"pk": single_art_project.pk})
    )
    content = response.json()
    assert content["data"]["type"] == "artProjects"


def test_polymorphism_on_detail_relations(single_company, client):
    response = client.get(reverse("company-detail", kwargs={"pk": single_company.pk}))
    content = response.json()
    assert (
        content["data"]["relationships"]["currentProject"]["data"]["type"]
        == "artProjects"
    )
    assert {
        rel["type"]
        for rel in content["data"]["relationships"]["futureProjects"]["data"]
    } == {"researchProjects", "artProjects"}


def test_polymorphism_on_included_relations(single_company, client):
    response = client.get(
        reverse("company-detail", kwargs={"pk": single_company.pk})
        + "?include=current_project,future_projects,current_art_project,current_research_project"
    )
    content = response.json()
    assert (
        content["data"]["relationships"]["currentProject"]["data"]["type"]
        == "artProjects"
    )
    assert (
        content["data"]["relationships"]["currentArtProject"]["data"]["type"]
        == "artProjects"
    )
    assert content["data"]["relationships"]["currentResearchProject"]["data"] is None
    assert {
        rel["type"]
        for rel in content["data"]["relationships"]["futureProjects"]["data"]
    } == {"researchProjects", "artProjects"}
    assert {x.get("type") for x in content.get("included")} == {
        "artProjects",
        "artProjects",
        "researchProjects",
    }, "Detail included types are incorrect"
    # Ensure that the child fields are present.
    assert content.get("included")[0].get("attributes").get("artist") is not None
    assert content.get("included")[1].get("attributes").get("artist") is not None
    assert content.get("included")[2].get("attributes").get("supervisor") is not None


def test_polymorphism_on_polymorphic_model_detail_patch(single_art_project, client):
    url = reverse("project-detail", kwargs={"pk": single_art_project.pk})
    response = client.get(url)
    content = response.json()
    test_topic = "test-{}".format(random.randint(0, 999999))
    test_artist = "test-{}".format(random.randint(0, 999999))
    content["data"]["attributes"]["topic"] = test_topic
    content["data"]["attributes"]["artist"] = test_artist
    response = client.patch(url, data=content)
    new_content = response.json()
    assert new_content["data"]["type"] == "artProjects"
    assert new_content["data"]["attributes"]["topic"] == test_topic
    assert new_content["data"]["attributes"]["artist"] == test_artist


def test_patch_on_polymorphic_model_without_including_required_field(
    single_art_project, client
):
    url = reverse("project-detail", kwargs={"pk": single_art_project.pk})
    data = {
        "data": {
            "id": single_art_project.pk,
            "type": "artProjects",
            "attributes": {"description": "New description"},
        }
    }
    response = client.patch(url, data)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["data"]["attributes"]["description"] == "New description"


def test_polymorphism_on_polymorphic_model_list_post(client):
    test_topic = "New test topic {}".format(random.randint(0, 999999))
    test_artist = "test-{}".format(random.randint(0, 999999))
    test_project_type = ProjectTypeFactory()
    url = reverse("project-list")
    data = {
        "data": {
            "type": "artProjects",
            "attributes": {"topic": test_topic, "artist": test_artist},
            "relationships": {
                "projectType": {
                    "data": {"type": "projectTypes", "id": test_project_type.pk}
                }
            },
        }
    }
    response = client.post(url, data=data)
    content = response.json()
    assert content["data"]["id"] is not None
    assert content["data"]["type"] == "artProjects"
    assert content["data"]["attributes"]["topic"] == test_topic
    assert content["data"]["attributes"]["artist"] == test_artist
    assert content["data"]["relationships"]["projectType"]["data"]["id"] == str(
        test_project_type.pk
    )


def test_polymorphism_on_polymorphic_model_w_included_serializers(client):
    test_project = ArtProjectFactory()
    query = "?include=projectType"
    url = reverse("project-list")
    response = client.get(url + query)
    content = response.json()
    assert content["data"][0]["id"] == str(test_project.pk)
    assert content["data"][0]["type"] == "artProjects"
    assert content["data"][0]["relationships"]["projectType"]["data"]["id"] == str(
        test_project.project_type.pk
    )
    assert content["included"][0]["type"] == "projectTypes"
    assert content["included"][0]["id"] == str(test_project.project_type.pk)


def test_polymorphic_model_without_any_instance(client):
    expected = {
        "links": {
            "first": "http://testserver/projects?page%5Bnumber%5D=1",
            "last": "http://testserver/projects?page%5Bnumber%5D=1",
            "next": None,
            "prev": None,
        },
        "data": [],
        "meta": {"pagination": {"page": 1, "pages": 1, "count": 0}},
    }

    response = client.get(reverse("project-list"))
    assert response.status_code == 200
    content = response.json()
    assert expected == content


def test_invalid_type_on_polymorphic_model(client):
    test_topic = "New test topic {}".format(random.randint(0, 999999))
    test_artist = "test-{}".format(random.randint(0, 999999))
    url = reverse("project-list")
    data = {
        "data": {
            "type": "invalidProjects",
            "attributes": {"topic": test_topic, "artist": test_artist},
        }
    }
    response = client.post(url, data=data)
    assert response.status_code == 409
    content = response.json()
    assert len(content["errors"]) == 1
    assert content["errors"][0]["status"] == "409"
    try:
        assert (
            content["errors"][0]["detail"]
            == "The resource object's type (invalidProjects) is not the type that constitute the "
            "collection represented by the endpoint (one of [researchProjects, artProjects])."
        )
    except AssertionError:
        # Available type list order isn't enforced
        assert (
            content["errors"][0]["detail"]
            == "The resource object's type (invalidProjects) is not the type that constitute the "
            "collection represented by the endpoint (one of [artProjects, researchProjects])."
        )


def test_polymorphism_relations_update(
    single_company, research_project_factory, client
):
    response = client.get(reverse("company-detail", kwargs={"pk": single_company.pk}))
    content = response.json()
    assert (
        content["data"]["relationships"]["currentProject"]["data"]["type"]
        == "artProjects"
    )

    research_project = research_project_factory()
    content["data"]["relationships"]["currentProject"]["data"] = {
        "type": "researchProjects",
        "id": research_project.pk,
    }
    response = client.patch(
        reverse("company-detail", kwargs={"pk": single_company.pk}), data=content
    )
    assert response.status_code == 200
    content = response.json()
    assert (
        content["data"]["relationships"]["currentProject"]["data"]["type"]
        == "researchProjects"
    )
    assert (
        int(content["data"]["relationships"]["currentProject"]["data"]["id"])
        == research_project.pk
    )


def test_polymorphism_relations_put_405(
    single_company, research_project_factory, client
):
    response = client.get(reverse("company-detail", kwargs={"pk": single_company.pk}))
    content = response.json()
    assert (
        content["data"]["relationships"]["currentProject"]["data"]["type"]
        == "artProjects"
    )

    research_project = research_project_factory()
    content["data"]["relationships"]["currentProject"]["data"] = {
        "type": "researchProjects",
        "id": research_project.pk,
    }
    response = client.put(
        reverse("company-detail", kwargs={"pk": single_company.pk}), data=content
    )
    assert response.status_code == 405


def test_invalid_type_on_polymorphic_relation(
    single_company, research_project_factory, client
):
    response = client.get(reverse("company-detail", kwargs={"pk": single_company.pk}))
    content = response.json()
    assert (
        content["data"]["relationships"]["currentProject"]["data"]["type"]
        == "artProjects"
    )

    research_project = research_project_factory()
    content["data"]["relationships"]["currentProject"]["data"] = {
        "type": "invalidProjects",
        "id": research_project.pk,
    }
    response = client.patch(
        reverse("company-detail", kwargs={"pk": single_company.pk}), data=content
    )
    assert response.status_code == 409
    content = response.json()
    assert len(content["errors"]) == 1
    assert content["errors"][0]["status"] == "409"
    try:
        assert (
            content["errors"][0]["detail"]
            == "Incorrect relation type. Expected one of [researchProjects, artProjects], "
            "received invalidProjects."
        )
    except AssertionError:
        # Available type list order isn't enforced
        assert (
            content["errors"][0]["detail"]
            == "Incorrect relation type. Expected one of [artProjects, researchProjects], "
            "received invalidProjects."
        )
