from rest_framework import serializers
from user_profiles.models import UserProfile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
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
            "password"
        ]

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
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["is_teacher"] = user.is_teacher
        token["student_id"] = user.student_id
        # Add other fields you need...

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data["token"] = str(refresh.access_token)
        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "is_teacher": self.user.is_teacher,
            "student_id": self.user.student_id
            # Add other fields you need...
        }
        return data
