from rest_framework import serializers
from courses.models import (
    Course,
    Class,
    Lab,
    Semester,
    LearningOutcome,
    LabLOContribution,
    Exercise,
    Submission,
    SubmissionFile,
)
from user_profiles.models import UserProfile
from django.db import transaction



class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
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
    course = serializers.PrimaryKeyRelatedField(read_only=True)

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


class ExerciseSerializer(serializers.ModelSerializer):
    outcome = LearningOutcomeSerializer(read_only=False)
    lab_name = LabSerializer(read_only=False)
    class Meta:
        model = Exercise
        fields = "__all__"
    
    def validate_class_code(self,class_code):
        try:
            return Class.objects.get(class_code=class_code)
        except Class.DoesNotExist:
            raise serializers.ValidationError("This class does not exist.")
    
    @transaction.atomic
    def create(self,validated_data):
        return self._handle_exercise_data(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        class_code = validated_data.get('class_code', instance.lab_name.class_code.class_code)  # Fallback to current instance
        target_class = self.validate_class_code(class_code)

        # Update or create the associated Outcome
        outcome_data = validated_data.pop('outcome', None)
        if outcome_data:
            outcome_serializer = LearningOutcomeSerializer(instance.outcome, data=outcome_data, partial=True)
            outcome_serializer.is_valid(raise_exception=True)
            outcome_serializer.save(course=target_class.course)
        else:
            instance.outcome.course = target_class.course
            instance.outcome.save()

        # Update or create the associated Lab
        lab_data = validated_data.pop('lab_name', None)
        if lab_data:
            lab_serializer = LabSerializer(instance.lab_name, data=lab_data, partial=True)
            lab_serializer.is_valid(raise_exception=True)
            lab_serializer.save(class_code=target_class)
        else:
            instance.lab_name.class_code = target_class
            instance.lab_name.save()

        # Update the exercise instance with remaining validated_data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def _handle_exercise_data(self, validated_data):
        class_code = validated_data.get('class_code')
        target_class = self.validate_class_code(class_code)

        outcome_data = validated_data.pop('outcome', {})
        outcome, _ = LearningOutcome.objects.get_or_create(course=target_class.course, defaults=outcome_data)

        lab_data = validated_data.pop('lab_name', {})
        lab, _ = Lab.objects.get_or_create(class_code=target_class, defaults=lab_data)

        exercise = Exercise.objects.create(outcome=outcome, lab_name=lab, **validated_data)
        return exercise
    

class SubmissionSerializer(serializers.ModelSerializer):
    exercise = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Submission
        fields = "__all__"


class SubmissionFileSerializer(serializers.ModelSerializer):
    class_code = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = SubmissionFile
        fields = "__all__"
        
    def validate_class_code(self,class_code):
        try:
            return Class.objects.get(class_code=class_code)
        except Class.DoesNotExist:
            raise serializers.ValidationError("This class does not exist.")
    
