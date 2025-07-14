from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication

class CustomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.authenticator = JWTAuthentication()

    def __call__(self, request):
        # Skip authentication for these exact paths
        open_paths = [
            '/login/',
            '/signup/',
            '/signup/verify-otp/',
            '/favicon.ico',
        ]

        # Skip authentication for anything under /admin/
        if request.path.startswith('/admin/') or request.path in open_paths:
            return self.get_response(request)

        try:
            userauth_tuple = self.authenticator.authenticate(request)
            if userauth_tuple is not None:
                request.user, _ = userauth_tuple
            else:
                request.user = None
        except Exception:
            return JsonResponse({"error": "Invalid token"}, status=401)

        if not request.user:
            return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)

        response = self.get_response(request)
        return response

