"""
Pagination fields
"""
# pylint: disable=no-init, too-few-public-methods, no-self-use


from rest_framework import serializers
from rest_framework import pagination
from rest_framework.views import Response
from rest_framework.templatetags.rest_framework import replace_query_param

# DRF 2.4.X compatibility.
ReadOnlyField = getattr(serializers, 'ReadOnlyField', serializers.Field)


class NextPageLinkField(ReadOnlyField):
    """
    Field that returns a link to the next page in paginated results.
    """
    page_field = 'page'

    def to_representation(self, value):
        if not value.has_next():
            return None
        page = value.next_page_number()
        request = self.context.get('request')
        url = request and request.build_absolute_uri() or ''
        return replace_query_param(url, self.page_field, page)


class NextPageField(ReadOnlyField):
    """
    Field that returns a link to the next page in paginated results.
    """
    page_field = 'page'

    def to_representation(self, value):
        if not value.has_next():
            return None
        return value.next_page_number()


class PreviousPageLinkField(ReadOnlyField):
    """
    Field that returns a link to the previous page in paginated results.
    """
    page_field = 'page'

    def to_representation(self, value):
        if not value.has_previous():
            return None
        page = value.previous_page_number()
        request = self.context.get('request')
        url = request and request.build_absolute_uri() or ''
        return replace_query_param(url, self.page_field, page)


class PreviousPageField(ReadOnlyField):
    """
    Field that returns a link to the previous page in paginated results.
    """
    page_field = 'page'

    def to_representation(self, value):
        if not value.has_previous():
            return None
        return value.previous_page_number()


class PageField(ReadOnlyField):
    """
    Field that returns a link to the previous page in paginated results.
    """
    page_field = 'page'

    def to_representation(self, value):
        return value.number


# compatibility for DRF 3.0 and older
try:
    BasePagination = pagination.PageNumberPagination
except:
    BasePagination = pagination.BasePaginationSerializer


class PaginationSerializer(BasePagination):
    """
    Pagination serializer.
    """
    next = NextPageField(source='*')
    next_link = NextPageLinkField(source='*')
    page = PageField(source='*')
    previous = PreviousPageField(source='*')
    previous_link = PreviousPageLinkField(source='*')
    count = ReadOnlyField(source='paginator.count')
    total = ReadOnlyField(source='paginator.num_pages')


class EmberPaginationSerializer(PaginationSerializer):
    """
    Backwards compatibility for name change
    """
    pass


class PageNumberPagination(BasePagination):
    """
    An Ember (soon to be json-api) compatible pagination format
    """
    def get_paginated_response(self, data):
        previous = None
        next = None
        if self.page.has_previous():
            previous = self.page.previous_page_number()
        if self.page.has_next():
            next = self.page.next_page_number()

        return Response({
            'results': data,
            'next': next,
            'next_link': self.get_next_link(),
            'page': self.page.number,
            'previous': previous,
            'previous_link': self.get_previous_link(),
            'count': self.page.paginator.count,
            'total': self.page.paginator.num_pages,
        })

