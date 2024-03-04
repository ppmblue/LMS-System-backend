from courses.models import Course, CourseTeacher, CourseSemester, Lab, LearningOutcome
from courses.serializers import (
    CourseSerializer,
    CourseSemesterSerializer,
    CourseTeacherSerializer,
    LabSerializer,
    LearningOutcomeSerializer,
)
from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from courses.permissions import IsLecturerOrHeadLecturer, IsTeachingCourse
from user_profiles.permissions import IsTeacher


class CourseList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_queryset(self):
        return Course.objects.filter(
            course_semester__semester_teacher__teacher=self.request.user
        )

    serializer_class = CourseSerializer

    def perform_create(self, serializer):
        serializer.save(creater=self.request.user)


class CourseDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsTeachingCourse]
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class CourseSemesterList(generics.ListCreateAPIView):
    permission_classes = [IsTeachingCourse]
    serializer_class = CourseSemesterSerializer
    lookup_url_kwarg = ["course_pk"]

    def get_queryset(self):
        course_pk = self.kwargs.get("course_pk")
        return CourseSemester.objects.filter(course__pk=course_pk)

    def perform_create(self, serializer):
        target_course = Course.objects.get(pk=self.kwargs.get("course_pk"))
        serializer.save(course=target_course)


class CourseSemesterDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsTeachingCourse]
    serializer_class = CourseSemesterSerializer
    queryset = CourseSemester.objects.all()
    lookup_url_kwarg = ["semester_name", "course_pk"]
    lookup_field = ["semester_name", "course_pk"]

    def get_object(self):
        course_pk = self.kwargs.get("course_pk")
        semester_name = self.kwargs.get("semester_name")
        queryset = self.get_queryset()
        obj = get_object_or_404(
            queryset, course__pk=course_pk, semester_name=semester_name
        )
        self.check_object_permissions(self.request, obj)
        return obj


class CourseTeacherList(generics.ListCreateAPIView):
    permission_classes = [IsTeachingCourse]
    serializer_class = CourseTeacherSerializer
    lookup_url_kwarg = ["course_pk"]

    def get_queryset(self):
        return CourseTeacher.objects.filter(
            course_semester__course__pk=self.kwargs.get("course_pk")
        )


class CourseTeacherDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsTeachingCourse]
    serializer_class = CourseTeacherSerializer
    queryset = CourseTeacher.objects.all()
    lookup_url_kwarg = ["pk", "course_pk"]
    lookup_field = ["pk", "course_pk"]

    def get_object(self):
        course_pk = self.kwargs.get("course_pk")
        teacher_pk = self.kwargs.get("teacher_pk")
        queryset = self.get_queryset()
        obj = get_object_or_404(
            queryset, course_semester__course__pk=course_pk, pk=teacher_pk
        )
        self.check_object_permissions(self.request, obj)
        return obj


class LabList(generics.ListCreateAPIView):
    permission_classes = [IsTeachingCourse]
    serializer_class = LabSerializer

    def get_queryset(self):
        course_pk = self.kwargs.get("course_pk")
        semester_name = self.kwargs.get("semester_name")
        return Lab.objects.filter(
            course_semester__semester_name=semester_name,
            course_semester__course__pk=course_pk,
        )

    def perform_create(self, serializer):
        course_pk = self.kwargs.get("course_pk")
        semester_name = self.kwargs.get("semester_name")
        try:
            target_semester = CourseSemester.objects.get(
                semester_name=semester_name, course__pk=course_pk
            )
        except CourseSemester.DoesNotExist as e:
            raise serializers.ValidationError({"semester": [str(e)]})
        serializer.save(course_semester=target_semester)


class LabDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsTeachingCourse]
    serializer_class = LabSerializer
    queryset = Lab.objects.all()
    lookup_url_kwarg = ["semester_name", "course_pk", "lab_pk"]
    lookup_field = ["semester_name", "course_pk", "lab_pk"]

    def get_object(self):
        course_pk = self.kwargs.get("course_pk")
        semester_name = self.kwargs.get("semester_name")
        lab_pk = self.kwargs.get("lab_pk")
        queryset = self.get_queryset()
        obj = get_object_or_404(
            queryset,
            course_semester__course__pk=course_pk,
            course_semester__semester_name=semester_name,
            pk=lab_pk,
        )
        self.check_object_permissions(self.request, obj)
        return obj
