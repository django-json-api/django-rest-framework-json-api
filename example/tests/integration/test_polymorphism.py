import pytest
import random
import json
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
    assert new_content["data"]["type"] == "artProjects"
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
    assert content["data"]["type"] == "artProjects"
    assert content['data']['attributes']['topic'] == test_topic
    assert content['data']['attributes']['artist'] == test_artist
