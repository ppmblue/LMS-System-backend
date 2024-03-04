from courses.models import Course, CourseTeacher, CourseSemester
from courses.serializers import (
    CourseSerializer,
    CourseSemesterSerializer,
    CourseTeacherSerializer,
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
    permission_classes = [IsAuthenticated, IsTeachingCourse]
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class CourseSemesterList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTeacher, IsTeachingCourse]
    serializer_class = CourseSemesterSerializer

    def get_queryset(self):
        course_pk = self.kwargs.get("pk")
        return CourseSemester.objects.filter(course__pk=course_pk)

    def perform_create(self, serializer):
        target_course = Course.objects.get(pk=self.kwargs.get("pk"))
        serializer.save(course=target_course)


class CourseSemesterDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsTeachingCourse]
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
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = CourseTeacherSerializer

    def get_queryset(self):
        return CourseTeacher.objects.filter(
            course_semester__course__pk=self.kwargs.get("pk")
        )
