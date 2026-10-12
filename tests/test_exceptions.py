import pytest
from django.http import Http404
from django.urls import reverse
from inline_snapshot import snapshot
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, ValidationError

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
