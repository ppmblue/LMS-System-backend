from rest_framework import serializers
from user_profiles.models import UserProfile
from courses.models import Course


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = [
            "email",
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "is_teacher",
        ]
        read_only_fields = ["username", "email", "is_teacher"]
