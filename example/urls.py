from django.urls import include, path, re_path
from rest_framework import routers

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
    QuestionnaireViewset,
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
router.register(r"questionnaires", QuestionnaireViewset)

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
]
