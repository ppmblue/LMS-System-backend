from rest_framework import serializers
from courses.models import Course, CourseTeacher, CourseSemester
from user_profiles.models import UserProfile


class CourseSerializer(serializers.ModelSerializer):
    creater = serializers.ReadOnlyField(source="creater.email")

    class Meta:
        model = Course
        fields = ["pk", "course_name", "department", "course_semester", "creater"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        course_pk = self.context["view"].kwargs.get("pk")
        if course_pk:
            self.fields["course_semester"] = serializers.PrimaryKeyRelatedField(
                many=True, queryset=CourseSemester.objects.filter(course__pk=course_pk)
            )


class CourseSemesterSerializer(serializers.ModelSerializer):
    course = serializers.ReadOnlyField(source="course.course_name")

    class Meta:
        model = CourseSemester
        fields = ("pk", "semester_name", "num_of_lab", "course")
        lookup_field = ["semester_name", "course"]


class CourseTeacherSerializer(serializers.ModelSerializer):
    teacher_fname = serializers.ReadOnlyField(source="teacher.first_name")
    teacher_email = serializers.ReadOnlyField(source="teacher.email")

    class Meta:
        model = CourseTeacher
        fields = (
            "pk",
            "teacher",
            "teacher_fname",
            "teacher_email",
            "course_semester",
            "role",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        course_pk = self.context["view"].kwargs.get("pk")
        if course_pk:
            self.fields["course_semester"] = serializers.PrimaryKeyRelatedField(
                many=True, queryset=CourseSemester.objects.filter(course__pk=course_pk)
            )

    def create(self, validated_data):
        teacher_data = validated_data.pop("teacher")
        course_semester_data = validated_data.pop("course_semester", [])
        try:
            teacher_instance = UserProfile.objects.get(pk=teacher_data.pk)
        except UserProfile.DoesNotExist as e:
            raise serializers.ValidationError({"teacher": [str(e)]})
        course_teacher = CourseTeacher.objects.create(
            **validated_data, teacher=teacher_instance
        )
        for cs_data in course_semester_data:
            try:
                target_course_semester = CourseSemester.objects.get(pk=cs_data.pk)
                course_teacher.course_semester.add(target_course_semester)
            except CourseSemester.DoesNotExist as e:
                course_teacher.delete()
                raise serializers.ValidationError({"course_semester": [str(e)]})
        return course_teacher
