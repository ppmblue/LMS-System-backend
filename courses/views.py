from courses.models import (
    Course,
    CourseTeacher,
    CourseSemester,
    Lab,
    LearningOutcome,
    LabLOContribution,
)
from rest_framework import exceptions, serializers


from courses.serializers import (
    CourseSerializer,
    CourseReadSerializer,
    CourseSemesterSerializer,
    CourseSemesterReadSerializer,
    CourseTeacherSerializer,
    LabSerializer,
    LearningOutcomeSerializer,
    LabLOContributionSerializer,
)
from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from courses.permissions import (
    IsLecturerOrHeadLecturer,
    IsTeacherForCourse,
    CanAccessSemesterObj,
    CanManageCourseData,
    CanManageLabData,
)
from user_profiles.permissions import IsTeacher


class CourseList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def get_serializer_class(self):
        if self.request.method in ["POST"]:
            return CourseSerializer
        return CourseReadSerializer

    def get_queryset(self):
        user = self.request.user

        if user.is_authenticated and user.is_teacher:
            if self.request.method in ["POST"]:
                queryset = Course.objects.filter(courseteacher_course__teacher=user)
            else:
                queryset = CourseTeacher.objects.filter(teacher=user).select_related(
                    "teacher"
                )
        else:
            if self.request.method in ["POST"]:
                queryset = Course.objects.none()
            else:
                queryset = CourseTeacher.objects.none()

        return queryset

    def perform_create(self, serializer):
        serializer.save(creater=self.request.user.email)


class CourseDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsTeacher, IsTeacherForCourse]
    serializer_class = CourseSerializer
    queryset = Course.objects.all()
    lookup_url_kwarg = ["course_code"]
    lookup_field = ["course_code"]

    def get_object(self):
        user = self.request.user
        queryset = self.get_queryset()
        course_code = self.kwargs.get("course_code")
        try:
            obj = get_object_or_404(queryset, course_code=course_code)
        except exceptions.NotFound:
            raise exceptions.NotFound("The requested course does not exist.")
        self.check_object_permissions(self.request, obj)
        return obj


class CourseSemesterList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_url_kwarg = ["course_code"]
    serializer_class = CourseSemesterSerializer

    def check_permissions(self, request):
        course_code = self.kwargs.get("course_code")
        return CourseTeacher.objects.get(
            course__course_code=course_code, teacher=request.user
        )

    def get_queryset(self):
        queryset = CourseSemester.objects.filter(
            course__course_code=self.kwargs.get("course_code")
        ).select_related("course")
        return queryset

    def perform_create(self, serializer):
        serializer.save(
            course=Course.objects.get(course_code=self.kwargs.get("course_code"))
        )


class CourseSemesterDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsTeacher, CanAccessSemesterObj]
    serializer_class = CourseSemesterSerializer
    lookup_url_kwarg = ["semester_name", "course_code"]
    lookup_field = ["semester_name", "course__course_code"]

    def get_serializer_class(self):
        if (self.request.method) in ["PUT", "PATCH", "DELETE"]:
            return CourseSemesterSerializer
        return CourseSemesterReadSerializer

    def get_object(self):
        course_code = self.kwargs.get("course_code")
        semester_name = self.kwargs.get("semester_name")
        obj = get_object_or_404(
            CourseSemester.objects.filter(
                course__course_code=course_code
            ).select_related("course"),
            semester_name=semester_name,
        )
        self.check_object_permissions(self.request, obj)
        return obj


class CourseTeacherList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, CanManageCourseData]
    lookup_url_kwarg = ["course_code"]
    serializer_class = CourseTeacherSerializer

    # def check_permissions(self):
    #     return (
    #         CourseTeacher.objects.filter(
    #             course=self.kwargs.get("course_code"), teacher=self.request.user
    #         )
    #         .select_related("teacher")
    #         .exists()
    #     )

    def get_queryset(self):
        return CourseTeacher.objects.filter(
            course__course_code=self.kwargs.get("course_code")
        ).prefetch_related("course_semester")

    def perform_create(self, serializer):
        target_course = Course.objects.get(course_code=self.kwargs.get("course_code"))
        serializer.save(course=target_course)


class CourseTeacherDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, CanManageCourseData]
    lookup_url_kwarg = ["pk", "course_code"]
    lookup_field = ["pk", "course__course_code"]
    serializer_class = CourseTeacherSerializer

    def get_object(self):
        course_code = self.kwargs.get("course_code")
        pk = self.kwargs.get("pk")

        queryset = CourseTeacher.objects.filter(
            course__course_code=course_code
        ).prefetch_related("course_semester")
        if not queryset.exists():
            raise exceptions.NotFound("The requested course does not exist")
        obj = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj


class LabList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, CanManageLabData]
    serializer_class = LabSerializer

    def get_queryset(self):
        course_code = self.kwargs.get("course_code")
        semester_name = self.kwargs.get("semester_name")
        return Lab.objects.filter(
            course_semester__semester_name=semester_name,
            course_semester__course__course_code=course_code,
        ).select_related("course_semester")

    def perform_create(self, serializer):
        course_code = self.kwargs.get("course_code")
        semester_name = self.kwargs.get("semester_name")
        try:
            target_semester = CourseSemester.objects.get(
                semester_name=semester_name, course__course_code=course_code
            )
        except CourseSemester.DoesNotExist as e:
            raise serializers.ValidationError({"semester": [str(e)]})
        serializer.save(course_semester=target_semester)


class LabDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, CanManageLabData]
    serializer_class = LabSerializer
    queryset = Lab.objects.all()
    lookup_url_kwarg = ["semester_name", "course_code", "lab_pk"]
    lookup_field = ["semester_name", "course_code", "lab_pk"]

    def get_object(self):
        course_code = self.kwargs.get("course_code")
        semester_name = self.kwargs.get("semester_name")
        lab_pk = self.kwargs.get("lab_pk")
        queryset = self.get_queryset()
        obj = get_object_or_404(
            queryset,
            course_semester__course__course_code=course_code,
            course_semester__semester_name=semester_name,
            pk=lab_pk,
        )
        self.check_object_permissions(self.request, obj)
        return obj


class LearningOutcomeList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, CanManageCourseData]
    serializer_class = LearningOutcomeSerializer
    lookup_url_kwarg = ["course_code"]

    def get_queryset(self):
        return LearningOutcome.objects.filter(
            course__course_code=self.kwargs.get("course_code")
        ).select_related("course")

    def perform_create(self, serializer):
        target_course = Course.objects.get(course_code=self.kwargs.get("course_code"))
        serializer.save(course=target_course)


class LearningOutcomeDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, CanManageCourseData]
    serializer_class = LearningOutcomeSerializer
    lookup_url_kwarg = ["course_code", "outcome_code"]

    def get_object(self):
        obj = get_object_or_404(
            LearningOutcome.objects.all().select_related("course"),
            course__course_code=self.kwargs.get("course_code"),
            outcome_code=self.kwargs.get("outcome_code"),
        )
        self.check_object_permissions(self.request, obj)
        return obj


class LabLOList(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, CanManageLabData]
    serializer_class = LabLOContributionSerializer
    lookup_url_kwarg = ["semester_name", "course_code", "lab_pk"]
    lookup_field = ["semester_name", "course_code", "lab_pk"]

    def get_queryset(self):
        course_code = self.kwargs.get("course_code")
        semester_name = self.kwargs.get("semester_name")
        return LabLOContribution.objects.filter(
            course_semester__semester_name=semester_name,
            course_semester__course__course_code=course_code,
            lab__lab_name=lab_pk,
        ).select_related("course_semester", "lab")

    def perform_create(self, serializer):
        course_code = self.kwargs.get("course_code")
        semester_name = self.kwargs.get("semester_name")
        lab_name = self.kwargs.get("lab_pk")
        try:
            target_lab = Lab.objects.get(
                course_semester__semester_name=semester_name,
                course_semester__course__course_code=course_code,
                lab_name=lab_name,
            )
        except Lab.DoesNotExist as e:
            raise serializers.ValidationError({"Lab": [str(e)]})

        serializer.save(
            lab=target_lab,
            course_semester=target_lab.course_semester,
        )


class LabLODetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, CanManageLabData]
    serializer_class = LabLOContributionSerializer
    lookup_url_kwarg = ["semester_name", "course_code", "lab_pk", "outcome_code"]
    lookup_field = ["semester_name", "course_code", "lab_pk", "outcome_code"]

    def get_object(self):
        course_code = self.kwargs.get("course_code")
        semester_name = self.kwargs.get("semester_name")
        lab_name = self.kwargs.get("lab_pk")
        outcome_code = self.kwargs.get("outcome_code")
        obj = get_object_or_404(
            LabLOContribution.objects.filter(
                course_semester__semester_name=semester_name,
                lab__lab_name=lab_name,
                course_semester__course__course_code=course_code,
            ).select_related("course_semester", "lab"),
            outcome__outcome_code=outcome_code,
        )
        self.check_object_permissions(self.request, obj)
        return obj
