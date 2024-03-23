from rest_framework import generics, serializers, exceptions
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .models import UserProfile
from user_profiles.serializers import UserProfileSerializer, MyTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class UserProfileDetail(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        user = self.request.user
        obj = get_object_or_404(UserProfile, pk=user.pk)
        self.check_object_permissions(self.request, obj)
        return obj


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
