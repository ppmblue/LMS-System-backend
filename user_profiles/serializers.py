from rest_framework import serializers
from user_profiles.models import UserProfile
from courses.models import Course
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = [
            "email",
            "username",
            "first_name",
            "last_name",
            "is_teacher",
            "phone_number",
            "student_id",
            "major",
        ]
        read_only_fields = ["username", "email", "is_teacher"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = UserProfile.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token["username"] = user.username
        token["email"] = user.email
        # ...

        return {"token": token.key, "user": user}
