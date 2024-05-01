from rest_framework import serializers
from courses.models import (
    Course,
    Class,
    Lab,
    Semester,
    LearningOutcome,
    LabLOContribution,
    Submission,
    SubmissionData
)
from user_profiles.models import UserProfile


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "pk",
            "course_code",
            "course_name",
            "department",
            "creator",
        ]
        read_only_fields = ["creator"]
        lookup_field = "course_code"

    # def get_course_semesters(self, instance):
    #     course_code = instance.pk or self.context["view"].kwargs.get("course_code")
    #     course_semesters = CourseSemester.objects.filter(
    #         course__course_code=course_code
    #     ).select_related("course")
    #     return course_semesters.values_list("semester_name", flat=True)


class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = ("pk", "semester_name")


class ClassSerializer(serializers.ModelSerializer):
    course = serializers.StringRelatedField(read_only=True)
    teacher = serializers.SlugRelatedField(
        queryset=UserProfile.objects.filter(),
        slug_field="email",
    )

    class Meta:
        model = Class
        fields = (
            "pk",
            "semester",
            "num_of_lab",
            "course",
            "teacher",
            "role",
            "class_code",
            "group",
        )
        lookup_field = ["course", "class_code"]
        read_only_fields = ["class_code"]


class LabSerializer(serializers.ModelSerializer):
    class_code = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Lab
        fields = (
            "id",
            "lab_name",
            "lab_type",
            "weight",
            "class_code",
        )
        lookup_field = ["class_code", "lab_name", "class_code"]


class LearningOutcomeSerializer(serializers.ModelSerializer):
    course = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = LearningOutcome
        fields = (
            "pk",
            "outcome_code",
            "outcome_name",
            "outcome_description",
            "course",
            "threshold",
            "parent_outcome",
        )
        lookup_field = ["course__course_code", "outcome_code"]


class LabLOContributionSerializer(serializers.ModelSerializer):
    lab = serializers.StringRelatedField(read_only=True)
    class_code = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = LabLOContribution
        fields = (
            "pk",
            "class_code",
            "lab",
            "outcome",
            "contribution_percentage",
        )
        lookup_field = [
            "class_code__class_code",
            "lab__lab_name",
            "outcome__outcome_code",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        course_code = self.context["view"].kwargs.get("course_code")
        if course_code:
            self.fields["outcome"] = serializers.SlugRelatedField(
                queryset=LearningOutcome.objects.filter(
                    course__course_code=course_code
                ).select_related("course"),
                slug_field="outcome_code",
            )


class SubmissionSerializer(serializers.ModelSerializer):
    submission_file = serializers.FileField(source='binaries')
    
    class Meta:
        model = Submission
        fields = ['class_code', 'submission_file']