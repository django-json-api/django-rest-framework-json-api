from django.conf import settings
from django.conf.urls import include, url
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
    NonPaginatedEntryViewSet,
    ProjectViewset
)

router = routers.DefaultRouter(trailing_slash=False)

router.register(r'blogs', BlogViewSet)
router.register(r'entries', EntryViewSet)
router.register(r'nopage-entries', NonPaginatedEntryViewSet, 'nopage-entry')
router.register(r'authors', AuthorViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'companies', CompanyViewset)
router.register(r'projects', ProjectViewset)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^entries/(?P<entry_pk>[^/.]+)/suggested/',
        EntryViewSet.as_view({'get': 'list'}),
        name='entry-suggested'
        ),
    url(r'^entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)',
        EntryRelationshipView.as_view(),
        name='entry-relationships'),
    url(r'^blogs/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)',
        BlogRelationshipView.as_view(),
        name='blog-relationships'),
    url(r'^comments/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)',
        CommentRelationshipView.as_view(),
        name='comment-relationships'),
    url(r'^authors/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)',
        AuthorRelationshipView.as_view(),
        name='author-relationships'),
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
