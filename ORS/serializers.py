from rest_framework import serializers
from .models import User ,Preference , EssentialItem , WardrobeItem , OutfitRecommendation
from django.contrib.auth import authenticate

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'age', 'gender']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user
    

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        data['user'] = user
        return data

class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = ['preference_name', 'preference_value']


class EssentialItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EssentialItem
        fields = '__all__'

class WardrobeItemSerializer(serializers.ModelSerializer):
    class Meta:
        model= WardrobeItem
        fields = ['id', 'user', 'name', 'category', 'color', 'material', 'size',
            'brand', 'description', 'image', 'season_suitability',
            'occasion_suitability', 'style_tags', 'pattern', 'fabric_density',
            'last_worn_date']
        read_only_fields = ['user'] 


class OutfitRequestSerializer(serializers.Serializer):
    
    occasion = serializers.CharField()
    preferred_styles = serializers.ListField(
        child=serializers.CharField(), required=False
    )
    color_themes = serializers.ListField(
        child=serializers.CharField(), required=False, allow_null=True
    )
    user_prompt = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField()
