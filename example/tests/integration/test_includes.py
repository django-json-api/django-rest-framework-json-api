import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_dynamic_related_data_is_included(single_entry, entry_factory, client):
    entry_factory()
    response = client.get(
        reverse("entry-detail", kwargs={"pk": single_entry.pk}) + "?include=featured"
    )
    included = response.json().get("included")

    assert [x.get("type") for x in included] == [
        "entries"
    ], "Dynamic included types are incorrect"
    assert (
        len(included) == 1
    ), "The dynamically included blog entries are of an incorrect count"


def test_dynamic_many_related_data_is_included(single_entry, entry_factory, client):
    entry_factory()
    response = client.get(
        reverse("entry-detail", kwargs={"pk": single_entry.pk}) + "?include=suggested"
    )
    included = response.json().get("included")

    assert included
    assert [x.get("type") for x in included] == [
        "entries"
    ], "Dynamic included types are incorrect"


def test_missing_field_not_included(author_bio_factory, author_factory, client):
    # First author does not have a bio
    author = author_factory(bio=None)
    response = client.get(reverse("author-detail", args=[author.pk]) + "?include=bio")
    content = response.json()
    assert "included" in content
    assert content["included"] == []
    # Second author does
    author = author_factory()
    response = client.get(reverse("author-detail", args=[author.pk]) + "?include=bio")
    data = response.json()
    assert "included" in data
    assert len(data["included"]) == 1
    assert data["included"][0]["attributes"]["body"] == author.bio.body


def test_deep_included_data_on_list(multiple_entries, client):
    response = client.get(
        reverse("entry-list") + "?include=comments,comments.author,"
        "comments.author.bio,comments.writer&page[size]=5"
    )
    included = response.json().get("included")

    assert len(response.json()["data"]) == len(
        multiple_entries
    ), "Incorrect entry count"
    assert [x.get("type") for x in included] == [
        "authorBios",
        "authorBios",
        "authors",
        "authors",
        "comments",
        "comments",
        "writers",
        "writers",
    ], "List included types are incorrect"

    comment_count = len(
        [resource for resource in included if resource["type"] == "comments"]
    )
    expected_comment_count = sum(entry.comments.count() for entry in multiple_entries)
    assert comment_count == expected_comment_count, "List comment count is incorrect"

    author_count = len(
        [resource for resource in included if resource["type"] == "authors"]
    )
    expected_author_count = sum(
        entry.comments.filter(author__isnull=False).count()
        for entry in multiple_entries
    )
    assert author_count == expected_author_count, "List author count is incorrect"

    author_bio_count = len(
        [resource for resource in included if resource["type"] == "authorBios"]
    )
    expected_author_bio_count = sum(
        entry.comments.filter(author__bio__isnull=False).count()
        for entry in multiple_entries
    )
    assert (
        author_bio_count == expected_author_bio_count
    ), "List author bio count is incorrect"

    writer_count = len(
        [resource for resource in included if resource["type"] == "writers"]
    )
    expected_writer_count = sum(
        entry.comments.filter(author__isnull=False).count()
        for entry in multiple_entries
    )
    assert writer_count == expected_writer_count, "List writer count is incorrect"

    # Also include entry authors
    response = client.get(
        reverse("entry-list") + "?include=authors,comments,comments.author,"
        "comments.author.bio&page[size]=5"
    )
    included = response.json().get("included")

    assert len(response.json()["data"]) == len(
        multiple_entries
    ), "Incorrect entry count"
    assert [x.get("type") for x in included] == [
        "authorBios",
        "authorBios",
        "authors",
        "authors",
        "authors",
        "authors",
        "comments",
        "comments",
    ], "List included types are incorrect"

    author_count = len(
        [resource for resource in included if resource["type"] == "authors"]
    )
    expected_author_count = sum(
        [entry.authors.count() for entry in multiple_entries]
        + [
            entry.comments.filter(author__isnull=False).count()
            for entry in multiple_entries
        ]
    )
    assert author_count == expected_author_count, "List author count is incorrect"


def test_deep_included_data_on_detail(single_entry, client):
    # Same test as in list but also ensures that intermediate resources (here comments' authors)
    # are returned along with the leaf nodes
    response = client.get(
        reverse("entry-detail", kwargs={"pk": single_entry.pk})
        + "?include=comments,comments.author.bio"
    )
    included = response.json().get("included")

    assert [x.get("type") for x in included] == [
        "authorBios",
        "authors",
        "comments",
    ], "Detail included types are incorrect"

    comment_count = len(
        [resource for resource in included if resource["type"] == "comments"]
    )
    expected_comment_count = single_entry.comments.count()
    assert comment_count == expected_comment_count, "Detail comment count is incorrect"

    author_bio_count = len(
        [resource for resource in included if resource["type"] == "authorBios"]
    )
    expected_author_bio_count = single_entry.comments.filter(
        author__bio__isnull=False
    ).count()
    assert (
        author_bio_count == expected_author_bio_count
    ), "Detail author bio count is incorrect"


def test_data_resource_not_included_again(single_comment, client):
    # This test makes sure that the resource which is in the data field is excluded
    # from the included field.
    response = client.get(
        reverse("comment-detail", kwargs={"pk": single_comment.pk})
        + "?include=entry.comments"
    )

    included = response.json().get("included")

    included_comments = [
        resource for resource in included if resource["type"] == "comments"
    ]
    assert single_comment.pk not in [
        int(x.get("id")) for x in included_comments
    ], "Resource of the data field duplicated in included"

    comment_count = len(included_comments)
    expected_comment_count = single_comment.entry.comments.count()
    # The comment in the data attribute must not be included again.
    expected_comment_count -= 1
    assert comment_count == expected_comment_count, "Comment count incorrect"


def test_meta_object_added_to_included_resources(single_entry, client):
    response = client.get(
        reverse("entry-detail", kwargs={"pk": single_entry.pk}) + "?include=comments"
    )
    assert response.json()["included"][0].get("meta")

    response = client.get(
        reverse("entry-detail", kwargs={"pk": single_entry.pk})
        + "?include=comments.author"
    )
    assert response.json()["included"][0].get("meta")
    assert response.json()["included"][1].get("meta")


def test_included_array_empty_when_requested_but_no_data(blog_factory, client):
    blog = blog_factory()
    response = client.get(
        reverse("blog-detail", kwargs={"pk": blog.pk}) + "?include=tags"
    )
    content = response.json()

    assert "included" in content
    assert content["included"] == []


def test_included_array_populated_when_related_data_exists(
    blog_factory, tagged_item_factory, client
):
    blog = blog_factory()
    tag = tagged_item_factory(tag="django")
    blog.tags.add(tag)

    response = client.get(
        reverse("blog-detail", kwargs={"pk": blog.pk}) + "?include=tags"
    )
    included = response.json()["included"]

    assert included, "Expected included array to be populated"
    assert [x.get("type") for x in included] == [
        "taggedItems"
    ], "Included types incorrect"
    assert included[0]["attributes"]["tag"] == "django"


def test_included_array_present_via_jsonapimeta_defaults(
    single_entry, comment_factory, author_factory, client
):
    author = author_factory()
    comment_factory(entry=single_entry, author=author)

    response = client.get(reverse("entry-detail", kwargs={"pk": single_entry.pk}))

    included = response.json()["included"]

    assert included, "Expected included array due to JSONAPIMeta defaults"
    assert any(resource["type"] == "comments" for resource in included)
