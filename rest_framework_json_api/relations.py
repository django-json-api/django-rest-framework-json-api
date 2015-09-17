from rest_framework.exceptions import ValidationError
from rest_framework.relations import *
from django.utils.translation import ugettext_lazy as _


class HyperlinkedRelatedField(HyperlinkedRelatedField):
    """
    This field exists for the sole purpose of accepting PKs as well as URLs
    when data is submitted back to the serializer
    """
    default_error_messages = {
        'required': _('This field is required.'),
        'no_match': _('Invalid hyperlink - No URL match.'),
        'incorrect_match': _('Invalid hyperlink - Incorrect URL match.'),
        'does_not_exist': _('Invalid hyperlink - Object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected URL string, received {data_type}.'),
        'pk_does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_pk_type': _('Incorrect type. Expected pk value, received {data_type}.'),
    }

    def __init__(self, **kwargs):
        self.pk_field = kwargs.pop('pk_field', None)
        super(HyperlinkedRelatedField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            # Try parsing links first for the browseable API
            return super(HyperlinkedRelatedField, self).to_internal_value(data)
        except ValidationError:
            if self.pk_field is not None:
                data = self.pk_field.to_internal_value(data)
            try:
                return self.get_queryset().get(pk=data)
            except ObjectDoesNotExist:
                self.fail('pk_does_not_exist', pk_value=data)
            except (TypeError, ValueError):
                self.fail('incorrect_pk_type', data_type=type(data).__name__)
