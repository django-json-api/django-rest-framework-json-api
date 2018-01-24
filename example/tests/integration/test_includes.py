import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_default_included_data_on_list(multiple_entries, client):
    return test_included_data_on_list(
        multiple_entries=multiple_entries, client=client, query='?page_size=5'
    )


def test_included_data_on_list(multiple_entries, client, query='?include=comments&page_size=5'):
    response = client.get(reverse("entry-list") + query)
    included = response.json().get('included')

    assert len(response.json()['data']) == len(multiple_entries), (
        'Incorrect entry count'
    )
    assert [x.get('type') for x in included] == ['comments', 'comments'], (
        'List included types are incorrect'
    )

    comment_count = len([resource for resource in included if resource["type"] == "comments"])
    expected_comment_count = sum([entry.comments.count() for entry in multiple_entries])
    assert comment_count == expected_comment_count, 'List comment count is incorrect'


def test_default_included_data_on_detail(single_entry, client):
    return test_included_data_on_detail(single_entry=single_entry, client=client, query='')


def test_included_data_on_detail(single_entry, client, query='?include=comments'):
    response = client.get(reverse("entry-detail", kwargs={'pk': single_entry.pk}) + query)
    included = response.json().get('included')

    assert [x.get('type') for x in included] == ['comments'], 'Detail included types are incorrect'

    comment_count = len([resource for resource in included if resource["type"] == "comments"])
    expected_comment_count = single_entry.comments.count()
    assert comment_count == expected_comment_count, 'Detail comment count is incorrect'


def test_dynamic_related_data_is_included(single_entry, entry_factory, client):
    entry_factory()
    response = client.get(
        reverse("entry-detail", kwargs={'pk': single_entry.pk}) + '?include=featured'
    )
    included = response.json().get('included')

    assert [x.get('type') for x in included] == ['entries'], 'Dynamic included types are incorrect'
    assert len(included) == 1, 'The dynamically included blog entries are of an incorrect count'


def test_dynamic_many_related_data_is_included(single_entry, entry_factory, client):
    entry_factory()
    response = client.get(
        reverse("entry-detail", kwargs={'pk': single_entry.pk}) + '?include=suggested'
    )
    included = response.json().get('included')

    assert included
    assert [x.get('type') for x in included] == ['entries'], 'Dynamic included types are incorrect'


def test_missing_field_not_included(author_bio_factory, author_factory, client):
    # First author does not have a bio
    author = author_factory(bio=None)
    response = client.get(reverse('author-detail', args=[author.pk]) + '?include=bio')
    assert 'included' not in response.json()
    # Second author does
    author = author_factory()
    response = client.get(reverse('author-detail', args=[author.pk]) + '?include=bio')
    data = response.json()
    assert 'included' in data
    assert len(data['included']) == 1
    assert data['included'][0]['attributes']['body'] == author.bio.body


def test_deep_included_data_on_list(multiple_entries, client):
    response = client.get(reverse("entry-list") + '?include=comments,comments.author,'
                          'comments.author.bio,comments.writer&page_size=5')
    included = response.json().get('included')

    assert len(response.json()['data']) == len(multiple_entries), (
        'Incorrect entry count'
    )
    assert [x.get('type') for x in included] == [
        'authorBios', 'authorBios', 'authors', 'authors',
        'comments', 'comments', 'writers', 'writers'
    ], 'List included types are incorrect'

    comment_count = len([resource for resource in included if resource["type"] == "comments"])
    expected_comment_count = sum([entry.comments.count() for entry in multiple_entries])
    assert comment_count == expected_comment_count, 'List comment count is incorrect'

    author_count = len([resource for resource in included if resource["type"] == "authors"])
    expected_author_count = sum(
        [entry.comments.filter(author__isnull=False).count() for entry in multiple_entries])
    assert author_count == expected_author_count, 'List author count is incorrect'

    author_bio_count = len([resource for resource in included if resource["type"] == "authorBios"])
    expected_author_bio_count = sum([entry.comments.filter(
        author__bio__isnull=False).count() for entry in multiple_entries])
    assert author_bio_count == expected_author_bio_count, 'List author bio count is incorrect'

    writer_count = len(
        [resource for resource in included if resource["type"] == "writers"]
    )
    expected_writer_count = sum(
        [entry.comments.filter(author__isnull=False).count() for entry in multiple_entries])
    assert writer_count == expected_writer_count, 'List writer count is incorrect'

    # Also include entry authors
    response = client.get(reverse("entry-list") + '?include=authors,comments,comments.author,'
                          'comments.author.bio&page_size=5')
    included = response.json().get('included')

    assert len(response.json()['data']) == len(multiple_entries), (
        'Incorrect entry count'
    )
    assert [x.get('type') for x in included] == [
        'authorBios', 'authorBios', 'authors', 'authors', 'authors', 'authors',
        'comments', 'comments'], 'List included types are incorrect'

    author_count = len([resource for resource in included if resource["type"] == "authors"])
    expected_author_count = sum(
        [entry.authors.count() for entry in multiple_entries] +
        [entry.comments.filter(author__isnull=False).count() for entry in multiple_entries])
    assert author_count == expected_author_count, 'List author count is incorrect'


def test_deep_included_data_on_detail(single_entry, client):
    # Same test as in list but also ensures that intermediate resources (here comments' authors)
    # are returned along with the leaf nodes
    response = client.get(reverse("entry-detail", kwargs={'pk': single_entry.pk}) +
                          '?include=comments,comments.author.bio')
    included = response.json().get('included')

    assert [x.get('type') for x in included] == ['authorBios', 'authors', 'comments'], \
        'Detail included types are incorrect'

    comment_count = len([resource for resource in included if resource["type"] == "comments"])
    expected_comment_count = single_entry.comments.count()
    assert comment_count == expected_comment_count, 'Detail comment count is incorrect'

    author_bio_count = len([resource for resource in included if resource["type"] == "authorBios"])
    expected_author_bio_count = single_entry.comments.filter(author__bio__isnull=False).count()
    assert author_bio_count == expected_author_bio_count, 'Detail author bio count is incorrect'
