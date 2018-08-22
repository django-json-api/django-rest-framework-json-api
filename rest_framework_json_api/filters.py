from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter

from rest_framework_json_api.utils import format_value


class JSONAPIOrderingFilter(OrderingFilter):
    """
    This implements http://jsonapi.org/format/#fetching-sorting and raises 400
    if any sort field is invalid. If you prefer *not* to report 400 errors for
    invalid sort fields, just use OrderingFilter with `ordering_param='sort'`

    TODO: Add sorting based upon relationships (sort=relname.fieldname)
    """
    ordering_param = 'sort'

    def remove_invalid_fields(self, queryset, fields, view, request):
        """
        overrides remove_invalid_fields to raise a 400 exception instead of
        silently removing them. set `ignore_bad_sort_fields = True` to not
        do this validation.
        """
        valid_fields = [
            item[0] for item in self.get_valid_fields(queryset, view,
                                                      {'request': request})
        ]
        bad_terms = [
            term for term in fields
            if format_value(term.lstrip('-'), "underscore") not in valid_fields
        ]
        if bad_terms:
            raise ValidationError('invalid sort parameter{}: {}'.format(
                ('s' if len(bad_terms) > 1 else ''), ','.join(bad_terms)))

        return super(JSONAPIOrderingFilter, self).remove_invalid_fields(
            queryset, fields, view, request)
