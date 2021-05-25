from django.conf import settings
from django.conf.urls import include, url
from django.urls import path
from django.views.generic import TemplateView
from rest_framework import routers
from rest_framework.schemas import get_schema_view

from rest_framework_json_api.schemas.openapi import SchemaGenerator

from example.views import (
    AuthorRelationshipView,
    AuthorViewSet,
    BlogRelationshipView,
    BlogViewSet,
    CommentRelationshipView,
    CommentViewSet,
    CompanyViewset,
    EntryRelationshipView,
    EntryViewSet,
    LabResultViewSet,
    NonPaginatedEntryViewSet,
    ProjectTypeViewset,
    ProjectViewset,
)

router = routers.DefaultRouter(trailing_slash=False)

router.register(r"blogs", BlogViewSet)
router.register(r"entries", EntryViewSet)
router.register(r"nopage-entries", NonPaginatedEntryViewSet, "nopage-entry")
router.register(r"authors", AuthorViewSet)
router.register(r"comments", CommentViewSet)
router.register(r"companies", CompanyViewset)
router.register(r"projects", ProjectViewset)
router.register(r"project-types", ProjectTypeViewset)
router.register(r"lab-results", LabResultViewSet)

urlpatterns = [
    url(r"^", include(router.urls)),
    url(
        r"^entries/(?P<entry_pk>[^/.]+)/suggested/$",
        EntryViewSet.as_view({"get": "list"}),
        name="entry-suggested",
    ),
    url(
        r"entries/(?P<entry_pk>[^/.]+)/blog$",
        BlogViewSet.as_view({"get": "retrieve"}),
        name="entry-blog",
    ),
    url(
        r"entries/(?P<entry_pk>[^/.]+)/comments$",
        CommentViewSet.as_view({"get": "list"}),
        name="entry-comments",
    ),
    url(
        r"entries/(?P<entry_pk>[^/.]+)/authors$",
        AuthorViewSet.as_view({"get": "list"}),
        name="entry-authors",
    ),
    url(
        r"entries/(?P<entry_pk>[^/.]+)/featured$",
        EntryViewSet.as_view({"get": "retrieve"}),
        name="entry-featured",
    ),
    url(
        r"^authors/(?P<pk>[^/.]+)/(?P<related_field>\w+)/$",
        AuthorViewSet.as_view({"get": "retrieve_related"}),
        name="author-related",
    ),
    url(
        r"^entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)$",
        EntryRelationshipView.as_view(),
        name="entry-relationships",
    ),
    url(
        r"^blogs/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)$",
        BlogRelationshipView.as_view(),
        name="blog-relationships",
    ),
    url(
        r"^comments/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)$",
        CommentRelationshipView.as_view(),
        name="comment-relationships",
    ),
    url(
        r"^authors/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)$",
        AuthorRelationshipView.as_view(),
        name="author-relationships",
    ),
    path(
        "openapi",
        get_schema_view(
            title="Example API",
            description="API for all things …",
            version="1.0.0",
            generator_class=SchemaGenerator,
        ),
        name="openapi-schema",
    ),
    path(
        "swagger-ui/",
        TemplateView.as_view(
            template_name="swagger-ui.html",
            extra_context={"schema_url": "openapi-schema"},
        ),
        name="swagger-ui",
    ),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        url(r"^__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
