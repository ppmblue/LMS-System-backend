from rest_framework import serializers
from courses.models import Course, CourseTeacher, CourseSemester, Lab, LearningOutcome
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
        lookup_field = ["course_code"]

    # def get_course_semesters(self, instance):
    #     course_code = instance.pk or self.context["view"].kwargs.get("course_code")
    #     course_semesters = CourseSemester.objects.filter(
    #         course__course_code=course_code
    #     ).select_related("course")
    #     return course_semesters.values_list("semester_name", flat=True)


class CourseReadSerializer(serializers.ModelSerializer):
    course = serializers.StringRelatedField(read_only=True)
    course_semester = serializers.SlugRelatedField(
        many=True,
        queryset=CourseSemester.objects.all(),
        slug_field="semester_name",
    )
    teacher = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CourseTeacher
        fields = ["course", "course_semester", "teacher"]


class CourseSemesterSerializer(serializers.ModelSerializer):
    course = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CourseSemester
        fields = ("pk", "semester_name", "num_of_lab", "course")
        lookup_field = ["semester_name", "course"]


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


class CourseTeacherSerializer(serializers.ModelSerializer):
    teacher = serializers.SlugRelatedField(
        queryset=UserProfile.objects.filter(),
        slug_field="email",
    )
    course = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CourseTeacher
        fields = (
            "pk",
            "teacher",
            "course_semester",
            "role",
            "course",
        )
        read_only_fields = ["course"]
        lookup_field = ["pk", "course__course_code"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        course_code = self.context["view"].kwargs.get("course_code")
        if course_code:
            self.fields["course_semester"] = serializers.SlugRelatedField(
                many=True,
                queryset=CourseSemester.objects.filter(
                    course__course_code=course_code
                ).select_related("course"),
                slug_field="semester_name",
            )

    def create(self, validated_data):
        course_semester_data = validated_data.pop("course_semester", [])
        course_teacher = CourseTeacher.objects.create(**validated_data)
        for cs_data in course_semester_data:
            try:
                target_course_semester = CourseSemester.objects.get(pk=cs_data.pk)
                course_teacher.course_semester.add(target_course_semester)
            except CourseSemester.DoesNotExist as e:
                course_teacher.delete()
                raise serializers.ValidationError({"course_semester": [str(e)]})
        return course_teacher


class LabSerializer(serializers.ModelSerializer):
    course_semester = serializers.ReadOnlyField(source="course_semester.semester_name")
    course = serializers.ReadOnlyField(source="course_semester.course.course_code")

    class Meta:
        model = Lab
        fields = ("lab_name", "lab_type", "weight", "course_semester", "course")
        lookup_field = ["semester_name", "course__course_code", "pk"]


class LearningOutcomeSerializer(serializers.ModelSerializer):
    course = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = LearningOutcome
        fields = ("pk", "outcome_code", "outcome_name", "outcome_description", "course")
        lookup_field = ["course__course_code", "outcome_code"]
