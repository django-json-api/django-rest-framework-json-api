import pytest
from django.urls import reverse
from rest_framework import status

from tests.models import BasicModel, ForeignKeySource, ForeignKeyTarget


@pytest.mark.urls("tests.urls")
class TestOrderingFilter:
    @pytest.mark.parametrize(
        "sort_param,expected",
        [
            # ascending sort
            ("text", ["1", "2", "3"]),
            # descending sort
            ("-text", ["3", "2", "1"]),
            # descending sort with two dashes should work
            ("--text", ["3", "2", "1"]),
        ],
    )
    def test_sort(self, db, client, sort_param, expected):
        BasicModel.objects.create(text="1")
        BasicModel.objects.create(text="3")
        BasicModel.objects.create(text="2")

        url = reverse("basicmodel-list")
        response = client.get(url, {"sort": sort_param, "page[size]": 3})
        result = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert [d["attributes"]["text"] for d in result["data"]] == expected

    @pytest.mark.parametrize(
        "sort_param,error",
        [
            (
                "nonesuch,text,-not-a-field",
                ["invalid sort parameters: nonesuch,-not-a-field"],
            )
        ],
    )
    def test_sort_invalid(self, db, client, sort_param, error):
        url = reverse("basicmodel-list")
        response = client.get(url, {"sort": sort_param, "page[size]": 3})
        result = response.json()

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert [e["detail"] for e in result["errors"]] == error

    @pytest.mark.parametrize(
        "format_type,sort_param,expected",
        [
            (False, "long_text", ["1", "2", "3"]),
            (False, "-long_text", ["3", "2", "1"]),
            ("underscore", "long_text", ["1", "2", "3"]),
            ("underscore", "-long_text", ["3", "2", "1"]),
            ("dasherize", "long-text", ["1", "2", "3"]),
            ("dasherize", "-long-text", ["3", "2", "1"]),
            ("camelize", "longText", ["1", "2", "3"]),
            ("camelize", "-longText", ["3", "2", "1"]),
            ("capitalize", "LongText", ["1", "2", "3"]),
            ("capitalize", "-LongText", ["3", "2", "1"]),
        ],
    )
    def test_sort_format(self, db, client, settings, format_type, sort_param, expected):
        settings.JSON_API_FORMAT_FIELD_NAMES = format_type

        BasicModel.objects.create(long_text="1")
        BasicModel.objects.create(long_text="3")
        BasicModel.objects.create(long_text="2")

        url = reverse("basicmodel-list")
        response = client.get(url, {"sort": sort_param, "page[size]": 3})
        result = response.json()

        assert response.status_code == status.HTTP_200_OK
        values = [d["attributes"][sort_param.lstrip("-")] for d in result["data"]]
        assert values == expected

    @pytest.mark.parametrize(
        "sort_param,expected",
        [
            ("target.name,name", ["1", "2", "3"]),
            ("-target.name,-name", ["3", "2", "1"]),
            ("target__name,name", ["1", "2", "3"]),
            ("-target__name,-name", ["3", "2", "1"]),
        ],
    )
    def test_sort_related(self, db, client, sort_param, expected):
        ForeignKeySource.objects.create(
            name="3", target=ForeignKeyTarget.objects.create(name="3")
        )
        ForeignKeySource.objects.create(
            name="1", target=ForeignKeyTarget.objects.create(name="1")
        )
        ForeignKeySource.objects.create(
            name="2", target=ForeignKeyTarget.objects.create(name="1")
        )

        url = reverse("foreignkeysource-list")
        response = client.get(url, {"sort": sort_param, "page[size]": 3})
        result = response.json()

        assert response.status_code == status.HTTP_200_OK
        values = [d["attributes"]["name"] for d in result["data"]]
        assert values == expected
