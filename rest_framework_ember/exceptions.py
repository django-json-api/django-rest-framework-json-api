from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)

    errors = []
    for field, error in response.data.items():
        for message in error:
            errors.append({
                'detail': message,
                'source': {
                    'parameter': field,
                },
            })
    context['view'].resource_name = 'errors'
    response.data = errors
    return response


