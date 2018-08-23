from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter

from rest_framework_json_api.utils import format_value


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
