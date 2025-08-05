"""
Custom middleware for the yoga flashcards project.
"""


class DisableCSRFMiddleware:
    """
    Middleware to disable CSRF protection for API routes in development.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return self.get_response(request)
