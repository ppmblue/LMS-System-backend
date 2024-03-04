from rest_framework import serializers
from user_profiles.models import UserProfile
from courses.models import Course


class UserSerializer(serializers.ModelSerializer):
    courses_created = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Course.objects.all()
    )

    class Meta:
        model = UserProfile
        fields = ["__all__", "courses_created"]
