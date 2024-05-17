from rest_framework import serializers
from students.models import Student

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['student_id', 'secured_student_id', 'first_name', 'last_name']