from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from .utils import generate_otp
from .serializers import UserSerializer
from .models import User
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
        serializer = UserSerializer(data=signup_data, context={"mode": "signup"})
        if serializer.is_valid():
            serializer.save()
            request.session.flush()  # Clear OTP and signup data
            return Response({"message": "Signup successful"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        # Pass login mode to serializer
        serializer = UserSerializer(data=request.data, context={"mode": "login"})

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