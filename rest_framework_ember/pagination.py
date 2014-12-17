from rest_framework import serializers
from rest_framework import pagination
from rest_framework.templatetags.rest_framework import replace_query_param

from rest_framework_ember.utils import get_resource_name


class NextPageLinkField(serializers.ReadOnlyField):
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


class NextPageField(serializers.ReadOnlyField):
    """
    Field that returns a link to the next page in paginated results.
    """
    page_field = 'page'

    def to_representation(self, value):
        if not value.has_next():
            return None
        return value.next_page_number()


class PreviousPageLinkField(serializers.ReadOnlyField):
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


class PreviousPageField(serializers.ReadOnlyField):
    """
    Field that returns a link to the previous page in paginated results.
    """
    page_field = 'page'

    def to_representation(self, value):
        if not value.has_previous():
            return None
        return value.previous_page_number()


class PageField(serializers.ReadOnlyField):
    """
    Field that returns a link to the previous page in paginated results.
    """
    page_field = 'page'

    def to_representation(self, value):
        return value.number



class PaginationSerializer(pagination.BasePaginationSerializer):
    next = NextPageField(source='*')
    next_link = NextPageLinkField(source='*')
    page = PageField(source='*')
    previous = PreviousPageField(source='*')
    previous_link = PreviousPageLinkField(source='*')
    count = serializers.ReadOnlyField(source='paginator.count')
    total = serializers.ReadOnlyField(source='paginator.num_pages')


class EmberPaginationSerializer(PaginationSerializer):
    """
    Backwards compatibility for name change
    """
    pass

