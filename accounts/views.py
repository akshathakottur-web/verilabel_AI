
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import SignInSerializer, SignUpSerializer, UserSerializer


class SignUpView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class SignInView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignInSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'error': 'Please enter your ID and password.'},
                            status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(
            username=serializer.validated_data['user_id'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response({'error': 'Invalid ID or password.'},
                            status=status.HTTP_401_UNAUTHORIZED)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user).data})


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
