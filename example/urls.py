from django.conf.urls import include, url
from rest_framework import routers

from example.views import BlogViewSet, EntryViewSet, AuthorViewSet, CommentViewSet, EntryRelationshipView, \
    EntryCommentViewSet

router = routers.DefaultRouter(trailing_slash=False)

router.register(r'blogs', BlogViewSet)
router.register(r'entries', EntryViewSet)
router.register(r'authors', AuthorViewSet)
router.register(r'comments', CommentViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),

    url(r'^entries/(?P<pk>[^/.]+)/comments/',
        EntryCommentViewSet.as_view({'get': 'list'}),
        name='entry-comment-list'),
    url(r'^entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)',
        EntryRelationshipView.as_view(),
        name='entry-relationships'),
]
