from django.urls import path
from .views import Signup_SendOTPView , Signup_VerifyOTP,LoginView

urlpatterns = [
    path('signup/', Signup_SendOTPView.as_view() , name="signup_sendotp"),
    path('signup/verify-otp/', Signup_VerifyOTP.as_view() , name= "Signup_verification"),
    path('login/', LoginView.as_view(), name ="login page")
]