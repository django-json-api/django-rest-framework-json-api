from django.conf import settings
from django.urls import include, path, re_path
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
    path("", include(router.urls)),
    re_path(
        r"^entries/(?P<entry_pk>[^/.]+)/suggested/$",
        EntryViewSet.as_view({"get": "list"}),
        name="entry-suggested",
    ),
    re_path(
        r"entries/(?P<entry_pk>[^/.]+)/blog$",
        BlogViewSet.as_view({"get": "retrieve"}),
        name="entry-blog",
    ),
    re_path(
        r"entries/(?P<entry_pk>[^/.]+)/comments$",
        CommentViewSet.as_view({"get": "list"}),
        name="entry-comments",
    ),
    re_path(
        r"entries/(?P<entry_pk>[^/.]+)/authors$",
        AuthorViewSet.as_view({"get": "list"}),
        name="entry-authors",
    ),
    re_path(
        r"entries/(?P<entry_pk>[^/.]+)/featured$",
        EntryViewSet.as_view({"get": "retrieve"}),
        name="entry-featured",
    ),
    re_path(
        r"^authors/(?P<pk>[^/.]+)/(?P<related_field>\w+)/$",
        AuthorViewSet.as_view({"get": "retrieve_related"}),
        name="author-related",
    ),
    re_path(
        r"^entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)$",
        EntryRelationshipView.as_view(),
        name="entry-relationships",
    ),
    re_path(
        r"^blogs/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)$",
        BlogRelationshipView.as_view(),
        name="blog-relationships",
    ),
    re_path(
        r"^comments/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)$",
        CommentRelationshipView.as_view(),
        name="comment-relationships",
    ),
    re_path(
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
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
