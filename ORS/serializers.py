from rest_framework import serializers
from .models import User ,Preference
from django.contrib.auth.hashers import make_password, check_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'first_name', 'last_name', 'email', 'password_hash', 'age', 'gender', 'created_at']
        read_only_fields = ['user_id', 'created_at']
    
    def validate(self, data):
        mode = self.context.get("mode")

        if mode == "signup":
            # Check if email already exists
            if User.objects.filter(email=data['email']).exists():                  #emailid check for signup
                raise serializers.ValidationError("Email is already registered.")
            return data

        elif mode == "login":
            try:
                user = User.objects.get(email=data['email'])                         #emailid check login
            except User.DoesNotExist:
                raise serializers.ValidationError("Email ID not registered.")

            if not check_password(data['password'], user.password_hash):               #password verification
                raise serializers.ValidationError("Incorrect password.")

            data['user'] = user  # pass user back to LoginView
            return data

        raise serializers.ValidationError("Invalid serializer mode.")
    
    def create(self, validated_data):                 #for signup only 
        return User.objects.create(
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data["email"],
            password_hash=make_password(validated_data["password"]),     #making hash password 
            age=validated_data.get("age"),    
            gender=validated_data.get("gender")
        )
    

class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = ['preference_name', 'preference_value']