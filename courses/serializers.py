from rest_framework import serializers
from courses.models import Course


class CourseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Course
        fields = ("pk", "course_name", "department", "num_of_lab")
