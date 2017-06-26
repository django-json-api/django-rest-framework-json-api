from django.conf.urls import include, url
from rest_framework import routers

from .api.resources.identity import GenericIdentity, Identity
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
    ProjectViewset
)

router = routers.DefaultRouter(trailing_slash=False)

router.register(r'blogs', BlogViewSet)
router.register(r'entries', EntryViewSet)
router.register(r'authors', AuthorViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'companies', CompanyViewset)
router.register(r'projects', ProjectViewset)

# for the old tests
router.register(r'identities', Identity)

urlpatterns = [
    url(r'^', include(router.urls)),

    # old tests
    url(r'identities/default/(?P<pk>\d+)',
        GenericIdentity.as_view(), name='user-default'),


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
