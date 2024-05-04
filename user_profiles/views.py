from rest_framework import generics, serializers, exceptions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import UserProfile
from user_profiles.serializers import UserProfileSerializer, MyTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from students.models import Student


class UserProfileDetail(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        user = self.request.user
        obj = get_object_or_404(UserProfile, pk=user.pk)
        self.check_object_permissions(self.request, obj)
        return obj


class Login(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def create(self, request, *args, **kwargs):
        student_id = request.data.get("student_id")
        if student_id:
            try:
                student = Student.objects.get(student_id=student_id)
            except Student.DoesNotExist:
                return Response(
                    {"error": "Student ID not found in system data."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not UserProfile.objects.filter(student_id=student_id):
                data = {
                    "username": request.data.get("username"),
                    "email": request.data.get("email"),
                    "first_name": student.first_name,
                    "last_name": student.last_name,
                    "phone_number": request.data.get("phone_number"),
                    "is_teacher": False,
                    "student_id": student.student_id,
                    "major": request.data.get("major"),
                    "password": request.data.get("password"),
                }
                serializer = self.get_serializer(data=data)
                if serializer.is_valid():
                    self.perform_create(serializer)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "Student account already exist!"})
        return Response(
            {"error": "Student ID is required."}, status=status.HTTP_400_BAD_REQUEST
        )
