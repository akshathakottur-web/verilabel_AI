
from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.validators import UnicodeUsernameValidator
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source='username')

    class Meta:
        model = User
        fields = ['name', 'user_id', 'role']


class SignUpSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    user_id = serializers.CharField(max_length=150, validators=[UnicodeUsernameValidator()])
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=['customer', 'inspector', 'admin'])

    def validate_user_id(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('This ID is already taken.')
        return value

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate_role(self, value):
        if value == 'admin' and not settings.ALLOW_ADMIN_SIGNUP:
            raise serializers.ValidationError('Admin accounts cannot be created here.')
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data['user_id'],
            password=validated_data['password'],
            name=validated_data['name'],
            role=validated_data['role'],
        )


class SignInSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    password = serializers.CharField()
