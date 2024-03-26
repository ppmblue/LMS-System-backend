from rest_framework import serializers
from courses.models import (
    Course,
    Class,
    Lab,
    Semester,
    LearningOutcome,
    LabLOContribution,
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
            "creater",
        ]
        read_only_fields = ["creater"]
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


# class CourseTeacherReadSerializer(serializers.ModelSerializer):
#     teacher_fname = serializers.ReadOnlyField(source="teacher.first_name")
#     teacher_email = serializers.ReadOnlyField(source="teacher.email")
#     course = serializers.ReadOnlyField(source="course.course_code")

#     class Meta:
#         model = CourseTeacher
#         fields = (
#             "pk",
#             "teacher",
#             "teacher_fname",
#             "teacher_email",
#             "role",
#             "course",
#             "teaching_semesters",
#         )
#         read_only_fields = ["course"]


# def __init__(self, *args, **kwargs):
#     super().__init__(*args, **kwargs)
#     course_pk = self.context["view"].kwargs.get("course_pk")
#     if course_pk:
#         self.fields["course_semester"] = serializers.PrimaryKeyRelatedField(
#             many=True, queryset=CourseSemester.objects.filter(course__pk=course_pk)
#         )


# class CourseTeacherSerializer(serializers.ModelSerializer):
#     teacher = serializers.SlugRelatedField(
#         queryset=UserProfile.objects.filter(),
#         slug_field="email",
#     )
#     course = serializers.StringRelatedField(read_only=True)

#     class Meta:
#         model = CourseTeacher
#         fields = (
#             "pk",
#             "teacher",
#             "role",
#             "course",
#         )
#         read_only_fields = ["course"]
#         lookup_field = ["pk", "course__course_code"]

# def __init__(self, *args, **kwargs):
#     super().__init__(*args, **kwargs)
#     course_code = self.context["view"].kwargs.get("course_code")
#     if course_code:
#         self.fields["course_semester"] = serializers.SlugRelatedField(
#             many=True,
#             queryset=CourseSemester.objects.filter(
#                 course__course_code=course_code
#             ).select_related("course"),
#             slug_field="semester_name",
#         )

# def create(self, validated_data):
#     course_semester_data = validated_data.pop("course_semester", [])
#     course_teacher = CourseTeacher.objects.create(**validated_data)
#     for cs_data in course_semester_data:
#         try:
#             target_course_semester = CourseSemester.objects.get(pk=cs_data.pk)
#             course_teacher.course_semester.add(target_course_semester)
#         except CourseSemester.DoesNotExist as e:
#             course_teacher.delete()
#             raise serializers.ValidationError({"course_semester": [str(e)]})
#     return course_teacher


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


# class CourseSemesterReadSerializer(serializers.ModelSerializer):
#     course = serializers.StringRelatedField(read_only=True)
#     lab_lo_contributions = serializers.SerializerMethodField()

#     class Meta:
#         model = CourseSemester
#         fields = ("pk", "semester_name", "num_of_lab", "course", "lab_lo_contributions")
#         lookup_field = ["semester_name", "course"]

#     def get_lab_lo_contributions(self, instance):
#         return (
#             LabLOContribution.objects.filter(course_semester=instance)
#             .select_related("course_semester", "lab", "outcome")
#             .values_list("lab", "outcome__outcome_code", "contribution_percentage")
#         )
