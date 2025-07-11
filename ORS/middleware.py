from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

class CustomMiddleware :
    def __init__(self, get_response):
        self.get_response = get_response
        self.authenticator = JWTAuthentication()

    def __call__(self, request ):
        if request.path in ['/login/', '/signup/','/signup/verify-otp/','/admin/']:
            return self.get_response(request)
        try :
            userauth_tuple = self.authenticator.authenticate(request)
            if userauth_tuple is not None:
                request.user,_ = userauth_tuple
            else:
                request.user =None
        
        except Exception as e:
            return JsonResponse({"error":"invalid token"},status = 401)
        
        if not request.user or not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)
        
        response = self.get_response(request)
        return response
