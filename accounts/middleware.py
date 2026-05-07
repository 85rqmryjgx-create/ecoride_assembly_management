from django.shortcuts import redirect

EXEMPT_PATHS = (
    '/accounts/complete-profile/',
    '/accounts/login/',
    '/accounts/logout/',
    '/static/',
    '/media/',
    '/init-setup/',
)


class ForceProfileCompleteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and getattr(request.user, 'must_change_password', False)
            and not any(request.path.startswith(p) for p in EXEMPT_PATHS)
        ):
            return redirect('accounts:complete_profile')
        return self.get_response(request)
