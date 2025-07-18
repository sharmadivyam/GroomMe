from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from .utils import generate_otp ,filter_wardrobe_items
from .serializers import SignupSerializer, LoginSerializer
from django.shortcuts import get_object_or_404
from .models import Preference, User , EssentialItem , WardrobeItem, OutfitRecommendation
from .serializers import PreferenceSerializer , EssentialItemSerializer, WardrobeItemSerializer,OutfitRequestSerializer
from rest_framework_simplejwt.tokens import RefreshToken
import google.generativeai as genai

genai.configure(api_key='AIzaSyBgJb17Jz6PMIxLk08Qlg49M9jRi6q5eBA')
model = genai.GenerativeModel(model_name ='models/gemini-1.5-flash')

class GeminiSuggestOutfit(APIView):
    def post(self, request):
        prompt = request.data.get('prompt')
        if not prompt:
            return Response({'error': 'Prompt is required'}, status=400)
        try:
            response = model.generate_content(prompt)
            return Response({'response': response.text}, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=500)

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
        serializer = SignupSerializer(data=signup_data)
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

class EssentialItemsListView(APIView):
    def get(self, request):
        essentials = EssentialItem.objects.all()
        serializer = EssentialItemSerializer(essentials, many=True)
        return Response(serializer.data)

class AddEssentialToWardrobeView(APIView):

    def post(self, request):
        essential_id = request.data.get("essential_id")
        user = request.user

        try:
            essential = EssentialItem.objects.get(id=essential_id)
        except EssentialItem.DoesNotExist:
            return Response({"error": "Essential not found."}, status=404)

        if WardrobeItem.objects.filter(user=user, essential_reference=essential).exists():
            return Response({"message": "Already added."}, status=200)

        WardrobeItem.objects.create(
            user=user,
            name=essential.name,
            category=essential.category,
            color=essential.color,
            material=essential.material,
            size=essential.size,
            brand=essential.brand,
            description=essential.description,
            image=essential.image,
            season_suitability=essential.season_suitability,
            occasion_suitability=essential.occasion_suitability,
            style_tags=essential.style_tags,
            pattern=essential.pattern,
            fabric_density=essential.fabric_density,
            is_basic_essential=True,
            essential_reference=essential
        )

        return Response({"message": "Added to wardrobe!"}, status=201)
    
class AddWardrobeItemView(APIView):

    def post(self, request):
        serializer = WardrobeItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"message": "Wardrobe item added!", "item": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def get(self, request):
        wardrobe_items = WardrobeItem.objects.filter(user=request.user)
        serializer = WardrobeItemSerializer(wardrobe_items, many=True)
        return Response({"items": serializer.data}, status=status.HTTP_200_OK)
    
    
class OutfitRecommendationView(APIView):
    def post(self, request):
        serializer = OutfitRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        user = request.user

         # Step 1: Fetch weather condition (mocking for now)
        weather_condition = "hot"

        filtered_items = filter_wardrobe_items(
            user=user,
            preferred_styles=data.get('preferred_styles'),
            occasion=data.get('occasion'),
            weather_condition=weather_condition,
        )

        print(f"Filtered items count: {len(filtered_items)}")
        for item in filtered_items:
            print(f"Item: {item.name} - {item.category} - {item.color}")

        #Step 2: creating an outfitrecommendation object (saving initial info)
        recommendation = OutfitRecommendation.objects.create(
            user=user,
            occasion=data["occasion"],
            preferred_styles=data.get("preferred_styles", []),
            color_themes=data.get("color_themes", []),
            user_prompt=data.get("user_prompt", ""),
            location=data["location"],
            weather_condition=weather_condition,
            conceptual_gen_ai_prompt_sent="",
            conceptual_gen_ai_description="",
            refined_gen_ai_prompt_sent="",
            gen_ai_description=""
        )


        prompt1 = (
        f"You are a fashion stylist. The user is looking for a conceptual idea of an outfit that suits the following context.\n\n"
        f"Crucially, this is only for inspiration — the outfit should not reference or depend on the user's actual clothes.\n"
        f"Instead, suggest a general outfit idea that matches the provided preferences:\n\n"
        f"OCCASION: {data['occasion']}\n"
        f"PREFERRED STYLES: {', '.join(data.get('preferred_styles', ['Any']))}\n"
        f"COLOR THEMES: {', '.join(data.get('color_themes', ['Any']))}\n"
        f"LOCATION: {data['location']}\n"
        f"WEATHER: {weather_condition}\n"
        f"USER NOTES: {data.get('user_prompt', 'None')}\n\n"
        f"Please provide:\n"
        f"1. A general outfit idea (e.g., top, bottom, footwear, accessories)\n"
        f"2. A short explanation of why this works for the occasion and weather\n"
        f"3. Optional styling tips to enhance the look\n\n"
        f"Do NOT use specific brand names or assume what the user owns. Keep it conceptual and adaptable.")

        try:
            response1 = model.generate_content(prompt1)               #using gena ai model defined at the top
            gen_description1 = response1.text
        except Exception as e:
            return Response({"error": f"Gemini failed: {str(e)}"}, status=500)

        recommendation.conceptual_gen_ai_prompt_sent = prompt1                       #saving the prompt and response in teh recommendation object
        recommendation.conceptual_gen_ai_description = gen_description1

        


        # Step 3: Generate a prompt from filtered items
        if filtered_items:
            item_descriptions = []
            for item in filtered_items:
                desc = f"- {item.name}"
                if item.category:
                    desc += f" (Category: {item.category})"
                if item.color:
                    desc += f" (Color: {item.color})"
                if item.material:
                    desc += f" (Material: {item.material})"
                if item.style_tags:
                    desc += f" (Style: {', '.join(item.style_tags)})"
                item_descriptions.append(desc)
            
            wardrobe_summary = "\n".join(item_descriptions)
        else:
            wardrobe_summary = "No suitable items found in wardrobe for the given preferences."

        # Step 4: Ask AI to build outfit using actual wardrobe
        prompt2 = (
            f"You are a personal stylist. The user already received a conceptual outfit idea:\n\n"
            f"\"{recommendation.conceptual_gen_ai_description}\"\n\n"
            f"Now, based on the user's actual wardrobe items below, suggest a complete outfit using only these items.\n\n"
            f"USER'S WARDROBE:\n{wardrobe_summary}\n\n"
            f"Please provide:\n"
            f"1. A complete outfit recommendation using only the provided items (include item names and categories)\n"
            f"2. Explanation of how this outfit aligns with the original idea\n"
            f"3. Any smart substitutions or styling adjustments made\n\n"
            f"If no close match is possible, suggest what items the user might consider adding."
        )
        try:
            response2 = model.generate_content(prompt2)               #using gena ai model defined at the top
            gen_description2 = response2.text
        except Exception as e:
            return Response({"error": f"Gemini failed: {str(e)}"}, status=500)
        
 
        recommendation.refined_gen_ai_prompt_sent = prompt2                      #saving the prompt and response in teh recommendation object
        recommendation.gen_ai_description= gen_description2
        recommendation.save()                             #saving the object in DB


        return Response({
        "message": "Outfit request received.",
        "recommendation_id": recommendation.id,
        "weather_condition": weather_condition,
        "conceptual_outfit": recommendation.conceptual_gen_ai_description,
        "final_outfit_recommendation": recommendation.gen_ai_description
    }, status=201)