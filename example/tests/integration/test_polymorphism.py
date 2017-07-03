import json
import random

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
    assert (
        set([rel["type"] for rel in content["data"]["relationships"]["futureProjects"]["data"]]) ==
        set(["researchProjects", "artProjects"])
    )


def test_polymorphism_on_included_relations(single_company, client):
    response = client.get(reverse("company-detail", kwargs={'pk': single_company.pk}) +
                          '?include=current_project,future_projects')
    content = load_json(response.content)
    assert content["data"]["relationships"]["currentProject"]["data"]["type"] == "artProjects"
    assert (
        set([rel["type"] for rel in content["data"]["relationships"]["futureProjects"]["data"]]) ==
        set(["researchProjects", "artProjects"])
    )
    assert set([x.get('type') for x in content.get('included')]) == set([
        'artProjects', 'artProjects', 'researchProjects']), 'Detail included types are incorrect'
    # Ensure that the child fields are present.
    assert content.get('included')[0].get('attributes').get('artist') is not None
    assert content.get('included')[1].get('attributes').get('artist') is not None
    assert content.get('included')[2].get('attributes').get('supervisor') is not None


def test_polymorphism_on_polymorphic_model_detail_patch(single_art_project, client):
    url = reverse("project-detail", kwargs={'pk': single_art_project.pk})
    response = client.get(url)
    content = load_json(response.content)
    test_topic = 'test-{}'.format(random.randint(0, 999999))
    test_artist = 'test-{}'.format(random.randint(0, 999999))
    content['data']['attributes']['topic'] = test_topic
    content['data']['attributes']['artist'] = test_artist
    response = client.patch(url, data=json.dumps(content), content_type='application/vnd.api+json')
    new_content = load_json(response.content)
    assert new_content['data']['type'] == "artProjects"
    assert new_content['data']['attributes']['topic'] == test_topic
    assert new_content['data']['attributes']['artist'] == test_artist


def test_polymorphism_on_polymorphic_model_list_post(client):
    test_topic = 'New test topic {}'.format(random.randint(0, 999999))
    test_artist = 'test-{}'.format(random.randint(0, 999999))
    url = reverse('project-list')
    data = {
        'data': {
            'type': 'artProjects',
            'attributes': {
                'topic': test_topic,
                'artist': test_artist
            }
        }
    }
    response = client.post(url, data=json.dumps(data), content_type='application/vnd.api+json')
    content = load_json(response.content)
    assert content['data']['id'] is not None
    assert content['data']['type'] == "artProjects"
    assert content['data']['attributes']['topic'] == test_topic
    assert content['data']['attributes']['artist'] == test_artist


def test_polymorphic_model_without_any_instance(client):
    expected = {
        "links": {
            "first": "http://testserver/projects?page=1",
            "last": "http://testserver/projects?page=1",
            "next": None,
            "prev": None
        },
        "data": [],
        "meta": {
            "pagination": {
                "page": 1,
                "pages": 1,
                "count": 0
            }
        }
    }

    response = client.get(reverse('project-list'))
    assert response.status_code == 200
    content = load_json(response.content)
    assert expected == content


def test_invalid_type_on_polymorphic_model(client):
    test_topic = 'New test topic {}'.format(random.randint(0, 999999))
    test_artist = 'test-{}'.format(random.randint(0, 999999))
    url = reverse('project-list')
    data = {
        'data': {
            'type': 'invalidProjects',
            'attributes': {
                'topic': test_topic,
                'artist': test_artist
            }
        }
    }
    response = client.post(url, data=json.dumps(data), content_type='application/vnd.api+json')
    assert response.status_code == 409
    content = load_json(response.content)
    assert len(content["errors"]) is 1
    assert content["errors"][0]["status"] == "409"
    try:
        assert content["errors"][0]["detail"] == \
            "The resource object's type (invalidProjects) is not the type that constitute the " \
            "collection represented by the endpoint (one of [researchProjects, artProjects])."
    except AssertionError:
        # Available type list order isn't enforced
        assert content["errors"][0]["detail"] == \
            "The resource object's type (invalidProjects) is not the type that constitute the " \
            "collection represented by the endpoint (one of [artProjects, researchProjects])."


def test_polymorphism_relations_update(single_company, research_project_factory, client):
    response = client.get(reverse("company-detail", kwargs={'pk': single_company.pk}))
    content = load_json(response.content)
    assert content["data"]["relationships"]["currentProject"]["data"]["type"] == "artProjects"

    research_project = research_project_factory()
    content["data"]["relationships"]["currentProject"]["data"] = {
        "type": "researchProjects",
        "id": research_project.pk
    }
    response = client.put(reverse("company-detail", kwargs={'pk': single_company.pk}),
                          data=json.dumps(content), content_type='application/vnd.api+json')
    assert response.status_code == 200
    content = load_json(response.content)
    assert content["data"]["relationships"]["currentProject"]["data"]["type"] == "researchProjects"
    assert int(content["data"]["relationships"]["currentProject"]["data"]["id"]) == \
        research_project.pk


def test_invalid_type_on_polymorphic_relation(single_company, research_project_factory, client):
    response = client.get(reverse("company-detail", kwargs={'pk': single_company.pk}))
    content = load_json(response.content)
    assert content["data"]["relationships"]["currentProject"]["data"]["type"] == "artProjects"

    research_project = research_project_factory()
    content["data"]["relationships"]["currentProject"]["data"] = {
        "type": "invalidProjects",
        "id": research_project.pk
    }
    response = client.put(reverse("company-detail", kwargs={'pk': single_company.pk}),
                          data=json.dumps(content), content_type='application/vnd.api+json')
    assert response.status_code == 409
    content = load_json(response.content)
    assert len(content["errors"]) is 1
    assert content["errors"][0]["status"] == "409"
    try:
        assert content["errors"][0]["detail"] == \
            "Incorrect relation type. Expected one of [researchProjects, artProjects], " \
            "received invalidProjects."
    except AssertionError:
        # Available type list order isn't enforced
        assert content["errors"][0]["detail"] == \
            "Incorrect relation type. Expected one of [artProjects, researchProjects], " \
            "received invalidProjects."
