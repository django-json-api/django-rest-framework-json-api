import pytest
from django.http import Http404
from django.urls import path, reverse
from inline_snapshot import snapshot
from rest_framework import generics, serializers, status
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.response import Response

from tests.serializers import BasicModelSerializer
from tests.views import BasicModelViewSet


@pytest.mark.urls("tests.urls")
@pytest.mark.parametrize(
    "viewname,data,errors",
    [
        # verify relationship error
        (
            "foreignkeysource-list",
            {"data": {"type": "ForeignKeySource", "attributes": {"name": "name"}}},
            snapshot(
                {
                    "errors": [
                        {
                            "detail": "This field is required.",
                            "status": "400",
                            "source": {"pointer": "/data/relationships/target"},
                            "code": "required",
                        },
                    ]
                }
            ),
        ),
        # verify attribute error
        (
            "basicmodel-list",
            {"data": {"type": "BasicModel", "attributes": {"text": "text"}}},
            snapshot(
                {
                    "errors": [
                        {
                            "detail": "This field is required.",
                            "status": "400",
                            "source": {"pointer": "/data/attributes/long_text"},
                            "code": "required",
                        },
                    ]
                }
            ),
        ),
    ],
)
def test_exception_handler_validation_errors(client, viewname, data, errors):
    url = reverse(viewname)
    response = client.post(url, data=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert errors == response.json()


@pytest.mark.parametrize(
    "format_type,pointer",
    [
        (False, "/data/attributes/long_text"),
        ("underscore", "/data/attributes/long_text"),
        ("dasherize", "/data/attributes/long-text"),
        ("camelize", "/data/attributes/longText"),
        ("capitalize", "/data/attributes/LongText"),
    ],
)
@pytest.mark.urls("tests.urls")
def test_exception_handler_validation_errors_format_attributes_pointer(
    client, format_type, pointer, settings
):
    """Check that attribute pointers are formatted correctly."""

    settings.JSON_API_FORMAT_FIELD_NAMES = format_type

    data = ({"data": {"type": "BasicModel", "attributes": {"text": "text"}}},)
    url = reverse("basicmodel-list")
    response = client.post(url, json=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert pointer == response.json()["errors"][0]["source"]["pointer"]


@pytest.mark.parametrize(
    "format_type,pointer",
    [
        (False, "/data/relationships/fk_source"),
        ("underscore", "/data/relationships/fk_source"),
        ("dasherize", "/data/relationships/fk-source"),
        ("camelize", "/data/relationships/fkSource"),
        ("capitalize", "/data/relationships/FkSource"),
    ],
)
@pytest.mark.urls("tests.urls")
def test_exception_handler_validation_errors_format_relationships_pointer(
    client, format_type, pointer, settings
):
    """Check that relationship pointers are formatted correctly."""

    settings.JSON_API_FORMAT_FIELD_NAMES = format_type

    data = (
        {
            "data": {
                "type": "NestedRelatedSource",
                "relationships": {"fk_source": {}},
            }
        },
    )
    url = reverse("nestedrelatedsource-list")
    response = client.post(url, json=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert pointer == response.json()["errors"][0]["source"]["pointer"]


@pytest.mark.urls("tests.urls")
@pytest.mark.parametrize(
    "error,expected",
    [
        (
            {"title": "Text too short", "detail": "Too short"},
            snapshot(
                {
                    "errors": [
                        {
                            "title": "Text too short",
                            "detail": "Too short",
                            "source": {"pointer": "/data/attributes/long_text"},
                            "status": "400",
                            "code": "invalid",
                        }
                    ]
                }
            ),
        ),
        (
            "Simple detail",
            snapshot(
                {
                    "errors": [
                        {
                            "detail": "Simple detail",
                            "status": "400",
                            "source": {"pointer": "/data/attributes/long_text"},
                            "code": "invalid",
                        }
                    ]
                }
            ),
        ),
    ],
)
def test_exception_handler_custom_field_validation(
    client, monkeypatch, error, expected
):
    def mock_validate_long_text(self, long_text):
        if len(long_text) < 5:
            raise ValidationError(error)

    monkeypatch.setattr(
        BasicModelSerializer,
        "validate_long_text",
        mock_validate_long_text,
        raising=False,
    )

    url = reverse("basicmodel-list")
    data = {
        "data": {
            "type": "BasicModel",
            "attributes": {"text": "text", "long_text": "1"},
        }
    }

    response = client.post(url, data=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert expected == response.json()


@pytest.mark.urls("tests.urls")
@pytest.mark.parametrize(
    "error,expected",
    [
        # simple ValidationError
        (
            "Simple error",
            snapshot(
                {
                    "errors": [
                        {
                            "detail": "Simple error",
                            "status": "400",
                            "source": {"pointer": "/data"},
                            "code": "invalid",
                        }
                    ]
                }
            ),
        ),
        # custom error
        (
            {"long_text": {"title": "Text too short", "detail": "Too short"}},
            snapshot(
                {
                    "errors": [
                        {
                            "title": "Text too short",
                            "detail": "Too short",
                            "source": {"pointer": "/data/attributes/long_text"},
                            "status": "400",
                            "code": "invalid",
                        }
                    ]
                }
            ),
        ),
    ],
)
def test_exception_handler_custom_serializer_validation(
    client, monkeypatch, error, expected
):
    def mock_validate(self, attrs):
        long_text = attrs["long_text"]
        if len(long_text) < 5:
            raise ValidationError(error)

    monkeypatch.setattr(
        BasicModelSerializer,
        "validate",
        mock_validate,
    )

    url = reverse("basicmodel-list")
    data = {
        "data": {
            "type": "BasicModel",
            "attributes": {"text": "text", "long_text": "1"},
        }
    }

    response = client.post(url, data=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert expected == response.json()


@pytest.mark.urls("tests.urls")
@pytest.mark.parametrize(
    "exception,expected",
    [
        # simple authentication failure
        (
            AuthenticationFailed("Token is invalid"),
            snapshot(
                {
                    "errors": [
                        {
                            "detail": "Token is invalid",
                            "status": "403",
                            "code": "authentication_failed",
                        }
                    ]
                }
            ),
        ),
        # authentication failed with custom error
        (
            AuthenticationFailed(
                {"detail": "Token is invalid", "code": "custom_authentication_failed"}
            ),
            snapshot(
                {
                    "errors": [
                        {
                            "detail": "Token is invalid",
                            "status": "403",
                            "code": "custom_authentication_failed",
                        }
                    ]
                }
            ),
        ),
        (
            Http404(),
            snapshot(
                {
                    "errors": [
                        {"detail": "Not found.", "status": "404", "code": "not_found"}
                    ]
                }
            ),
        ),
    ],
)
def test_exception_handler_different_exceptions(
    client, monkeypatch, exception, expected, settings
):
    def mock_perform_create(self, serializer):
        raise exception

    monkeypatch.setattr(
        BasicModelViewSet,
        "perform_create",
        mock_perform_create,
    )

    url = reverse("basicmodel-list")
    data = {
        "data": {
            "type": "BasicModel",
            "attributes": {"text": "text", "long_text": "1"},
        }
    }
    response = client.post(url, data=data)

    assert response.json() == expected


@pytest.mark.urls(__name__)
@pytest.mark.parametrize(
    "data,format_type,pointer",
    [
        # check nested serializer with no formatting
        (
            {
                "data": {
                    "type": "entries",
                    "attributes": {
                        "text": "text",
                        "nested": {},
                    },
                }
            },
            False,
            "/data/attributes/nested/nested_text",
        ),
        # check nested list serializer with camelize
        # nested values are not JSON:API fields and therefore nested_text is not formatted
        (
            {
                "data": {
                    "type": "entries",
                    "attributes": {
                        "text": "text",
                        "nested_many": [{}],
                    },
                }
            },
            "camelize",
            "/data/attributes/nestedMany/0/nested_text",
        ),
        # check deeply nested list serializer
        (
            {
                "data": {
                    "type": "entries",
                    "attributes": {
                        "text": "text",
                        "nested_many": [
                            {"nested_text": "text", "deeply_nested_many": [{}]}
                        ],
                    },
                }
            },
            False,
            "/data/attributes/nested_many/0/deeply_nested_many/0/deeply_nested_text",
        ),
        # check deeply nested serializer
        (
            {
                "data": {
                    "type": "entries",
                    "attributes": {
                        "text": "text",
                        "nested_many": [{"nested_text": "text", "deeply_nested": {}}],
                    },
                }
            },
            False,
            "/data/attributes/nested_many/0/deeply_nested/deeply_nested_text",
        ),
    ],
)
def test_exception_handler_nested_serializer_pointer(
    client, settings, data, format_type, pointer
):
    settings.JSON_API_FORMAT_FIELD_NAMES = format_type

    url = reverse("entries-nested-list")
    response = client.post(url, data=data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    result = response.json()
    assert "errors" in result
    errors = result["errors"]
    assert len(errors) == 1

    assert errors[0]["source"]["pointer"] == pointer


@pytest.mark.urls("tests.urls")
def test_exception_handler_empty_response(client, monkeypatch):
    def mock_list(self, request, *args, **kwargs):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    monkeypatch.setattr(
        BasicModelViewSet,
        "list",
        mock_list,
    )

    url = reverse("basicmodel-list")
    response = client.get(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data is None


# Routing setup


class DeeplyNestedSerializer(serializers.Serializer):
    deeply_nested_text = serializers.CharField(allow_null=False, required=True)


class NestedSerializer(serializers.Serializer):
    deeply_nested_many = DeeplyNestedSerializer(many=True, required=False)
    deeply_nested = DeeplyNestedSerializer(required=False)
    nested_text = serializers.CharField(allow_null=True, required=True)


class EntrySerializer(serializers.Serializer):
    nested_many = NestedSerializer(many=True, required=False)
    nested = NestedSerializer(required=False)
    text = serializers.CharField(allow_null=True, required=True)


class EntryTestView(generics.CreateAPIView):
    serializer_class = EntrySerializer
    resource_name = "entries"

    def get_serializer_context(self):
        return {}


urlpatterns = [
    path("entries-nested", EntryTestView.as_view(), name="entries-nested-list")
]
