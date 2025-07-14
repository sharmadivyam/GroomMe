from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from .utils import generate_otp
from .serializers import SignupSerializer, LoginSerializer
from django.shortcuts import get_object_or_404
from .models import Preference, User
from .serializers import PreferenceSerializer
from rest_framework_simplejwt.tokens import RefreshToken

class Signup_SendOTPView(APIView):

    def post(self, request):
        """Step 1: Send OTP and store user data temporarily"""
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        otp = generate_otp()

        # Save OTP and signup data in session
        request.session['otp'] = otp
        request.session['email'] = email
        request.session['signup_data'] = request.data  # Store full signup data

        send_mail(
            subject='Your OTP Code',
            message=f'Your OTP is {otp}',
            from_email='ds906@snu.edu.in',
            recipient_list=[email],
        )

        return Response({"message": "OTP sent to your email"}, status=status.HTTP_200_OK)
    

class Signup_VerifyOTP(APIView):

    def post(self, request):
        """Step 2: Verify OTP and create user"""
        user_otp = request.data.get('otp')
        session_otp = request.session.get('otp')
        signup_data = request.session.get('signup_data')

        if not user_otp:
            return Response({"error": "OTP is required"}, status=status.HTTP_400_BAD_REQUEST)

        if user_otp != session_otp:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # OTP verified → create user using stored signup data
        serializer = Signup_SendOTPView(data=signup_data)
        if serializer.is_valid():
            serializer.save()
            request.session.flush()  # Clear OTP and signup data
            return Response({"message": "Signup successful"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        # Pass login mode to serializer
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            request.session['access_token'] = access_token
            request.session['username'] = user.email

            print("Login Successful")

            response = Response({
                "status": 202,
                "message": "Login Successful",
                "username": user.email,
                "user_id": user.user_id,
                "token": {
                    "access": access_token,
                    "refresh": str(refresh)
                }
            }, status=status.HTTP_202_ACCEPTED)

            response['Authorization'] = f'Bearer {access_token}'

            return response

        print("Serializer Errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class PreferenceSaveView(APIView):
    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        preferences_data = request.data  # list of preferences

        for item in preferences_data:
            serializer = PreferenceSerializer(data=item)
            if serializer.is_valid():
                pref_name = serializer.validated_data['preference_name']
                new_values = serializer.validated_data['preference_value']

                # Tries to get existing Preference (we'll merge if it exists)
                try:
                    preference = Preference.objects.get(user=user, preference_name=pref_name)
                    existing_values = preference.preference_value or []
                    merged_values = list(set(existing_values + new_values))
                except Preference.DoesNotExist:
                    merged_values = new_values

                # Now update or create using merged values
                Preference.objects.update_or_create(
                    user=user,
                    preference_name=pref_name,
                    defaults={'preference_value': merged_values}
                )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Preferences saved or updated successfully."}, status=status.HTTP_201_CREATED)
