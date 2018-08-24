import re

from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.settings import api_settings

from rest_framework_json_api.utils import format_value

try:
    from django_filters.rest_framework import DjangoFilterBackend
except ImportError as e:
    class DjangoFilterBackend(object):
        def __init__(self):
            raise ImportError("must install django-filter package to use JSONAPIDjangoFilter")


class JSONAPIOrderingFilter(OrderingFilter):
    """
    This implements http://jsonapi.org/format/#fetching-sorting and raises 400
    if any sort field is invalid. If you prefer *not* to report 400 errors for
    invalid sort fields, just use OrderingFilter with `ordering_param='sort'`

    Also applies DJA format_value() to convert (e.g. camelcase) to underscore.
    (See JSON_API_FORMAT_FIELD_NAMES in docs/usage.md)
    """
    ordering_param = 'sort'

    def remove_invalid_fields(self, queryset, fields, view, request):
        valid_fields = [
            item[0] for item in self.get_valid_fields(queryset, view,
                                                      {'request': request})
        ]
        bad_terms = [
            term for term in fields
            if format_value(term.replace(".", "__").lstrip('-'), "underscore") not in valid_fields
        ]
        if bad_terms:
            raise ValidationError('invalid sort parameter{}: {}'.format(
                ('s' if len(bad_terms) > 1 else ''), ','.join(bad_terms)))
        # this looks like it duplicates code above, but we want the ValidationError to report
        # the actual parameter supplied while we want the fields passed to the super() to
        # be correctly rewritten.
        # The leading `-` has to be stripped to prevent format_value from turning it into `_`.
        underscore_fields = []
        for item in fields:
            item_rewritten = item.replace(".", "__")
            if item_rewritten.startswith('-'):
                underscore_fields.append(
                    '-' + format_value(item_rewritten.lstrip('-'), "underscore"))
            else:
                underscore_fields.append(format_value(item_rewritten, "underscore"))

        return super(JSONAPIOrderingFilter, self).remove_invalid_fields(
            queryset, underscore_fields, view, request)


class JSONAPIDjangoFilter(DjangoFilterBackend):
    """
    A Django-style ORM filter implementation, using `django-filter`.

    This is not part of the jsonapi standard per-se, other than the requirement
    to use the `filter` keyword: This is an optional implementation of style of
    filtering in which each filter is an ORM expression as implemented by
    DjangoFilterBackend and seems to be in alignment with an interpretation of
    http://jsonapi.org/recommendations/#filtering, including relationship
    chaining. It also returns a 400 error for invalid filters.

    Filters can be:
    - A resource field equality test:
        `?filter[qty]=123`
    - Apply other [field lookup](https://docs.djangoproject.com/en/stable/ref/models/querysets/#field-lookups)  # noqa: E501
      operators:
        `?filter[name.icontains]=bar` or `?filter[name.isnull]=true...`
    - Membership in a list of values:
        `?filter[name.in]=abc,123,zzz (name in ['abc','123','zzz'])`
    - Filters can be combined for intersection (AND):
        `?filter[qty]=123&filter[name.in]=abc,123,zzz&filter[...]`
    - A related resource path can be used:
    `?filter[inventory.item.partNum]=123456 (where `inventory.item` is the relationship path)`

    If you are also using rest_framework.filters.SearchFilter you'll want to customize
    the name of the query parameter for searching to make sure it doesn't conflict
    with a field name defined in the filterset.
    The recommended value is: `search_param="filter[search]"` but just make sure it's
    `filter[<something>]` to comply with the jsonapi spec requirement to use the filter
    keyword. The default is "search" unless overriden but it's used here just to make sure
    we don't complain about it being an invalid filter.

    TODO: find a better way to deal with search_param.
    """
    search_param = api_settings.SEARCH_PARAM
    # since 'filter' passes query parameter validation but is still invalid,
    # make this regex check for it but not set `filter` regex group.
    filter_regex = re.compile(r'^filter(?P<ldelim>\W*)(?P<assoc>[\w._]*)(?P<rdelim>\W*$)')

    def validate_filter(self, keys, filterset_class):
        for k in keys:
            if ((not filterset_class) or (k not in filterset_class.base_filters)):
                raise ValidationError("invalid filter[{}]".format(k))

    def get_filterset(self, request, queryset, view):
        """
        Sometimes there's no filterset_class defined yet the client still
        requests a filter. Make sure they see an error too. This means
        we have to get_filterset_kwargs() even if there's no filterset_class.

        TODO: .base_filters vs. .filters attr (not always present)
        """
        filterset_class = self.get_filterset_class(view, queryset)
        kwargs = self.get_filterset_kwargs(request, queryset, view)
        self.validate_filter(self.filter_keys, filterset_class)
        if filterset_class is None:
            return None
        return filterset_class(**kwargs)

    def get_filterset_kwargs(self, request, queryset, view):
        """
        Turns filter[<field>]=<value> into <field>=<value> which is what
        DjangoFilterBackend expects
        """
        self.filter_keys = []
        # rewrite filter[field] query params to make DjangoFilterBackend work.
        data = request.query_params.copy()
        for qp, val in data.items():
            m = self.filter_regex.match(qp)
            if m and (not m.groupdict()['assoc'] or
                      m.groupdict()['ldelim'] != '[' or m.groupdict()['rdelim'] != ']'):
                raise ValidationError("invalid filter: {}".format(qp))
            if m and qp != self.search_param:
                if not val:
                    raise ValidationError("missing {} test value".format(qp))
                # convert jsonapi relationship path to Django ORM's __ notation
                key = m.groupdict()['assoc'].replace('.', '__')
                # undo JSON_API_FORMAT_FIELD_NAMES conversion:
                key = format_value(key, 'underscore')
                data[key] = val
                self.filter_keys.append(key)
                del data[qp]
        return {
            'data': data,
            'queryset': queryset,
            'request': request,
        }

    def filter_queryset(self, request, queryset, view):
        """
        backwards compatibility to 1.1
        """
        filter_class = self.get_filter_class(view, queryset)

        kwargs = self.get_filterset_kwargs(request, queryset, view)
        self.validate_filter(self.filter_keys, filter_class)

        if filter_class:
            return filter_class(kwargs['data'], queryset=queryset, request=request).qs

        return queryset
