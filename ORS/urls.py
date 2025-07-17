from django.urls import path
from .views import Signup_SendOTPView , Signup_VerifyOTP,LoginView , PreferenceSaveView , GeminiSuggestOutfit , EssentialItemsListView, AddEssentialToWardrobeView, AddWardrobeItemView,OutfitRecommendationView

urlpatterns = [
    path('signup/', Signup_SendOTPView.as_view() , name="signup_sendotp"),
    path('signup/verify-otp/', Signup_VerifyOTP.as_view() , name= "Signup_verification"),
    path('login/', LoginView.as_view(), name ="login page"),
    path('api/users/<int:user_id>/preferences/', PreferenceSaveView.as_view(), name="initial preferences"),
    path('ai/suggest/', GeminiSuggestOutfit.as_view(), name='gemini-suggest'),
    path('essentials/', EssentialItemsListView.as_view(), name='essentials-list'),
    path('wardrobe/add-essential/', AddEssentialToWardrobeView.as_view(), name='adding from essential to wardrobe'),
    path('wardrobe/' , AddWardrobeItemView.as_view() , name="add to wardrobe" ),
    path('generate-outfit/', OutfitRecommendationView.as_view(), name='generate-outfit'),
]