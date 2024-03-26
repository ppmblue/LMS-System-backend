from courses.models import (
    Course,
    Semester,
    Class,
    Lab,
    LearningOutcome,
    LabLOContribution,
)
from rest_framework import exceptions, serializers, status
from rest_framework.response import Response


from courses.serializers import (
    CourseSerializer,
    SemesterSerializer,
    ClassSerializer,
    LabSerializer,
    LearningOutcomeSerializer,
    LabLOContributionSerializer,
)
from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from user_profiles.permissions import IsTeacher


class CourseList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def perform_create(self, serializer):
        serializer.save(creater=self.request.user.email)


class CourseDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = CourseSerializer
    queryset = Course.objects.all()
    lookup_field = "course_code"

    # def get_object(self):
    #     user = self.request.user
    #     queryset = self.get_queryset()
    #     course_code = self.akwargs.get("course_code")
    #     try:
    #         obj = get_object_or_404(queryset, course_code=course_code)
    #     except exceptions.NotFound:
    #         raise exceptions.NotFound("The requested course does not exist.")
    #     self.check_object_permissions(self.request, obj)
    #     return obj


class ClassList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    lookup_url_kwarg = ["course_code"]
    serializer_class = ClassSerializer

    def get_queryset(self):
        course_code = self.kwargs.get("course_code")
        semester_name = self.request.query_params.get("semester")
        queryset = Class.objects.all()
        try:
            target_course = Course.objects.get(course_code=course_code)
            queryset = queryset.filter(course__course_code=course_code).select_related(
                "course"
            )
            if semester_name:
                queryset = queryset.filter(semester=semester_name)
        except Course.DoesNotExist as e:
            raise serializers.ValidationError({"Course": [str(e)]})
        return queryset

    def perform_create(self, serializer):
        serializer.save(
            course=Course.objects.get(course_code=self.kwargs.get("course_code"))
        )


class ClassDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ClassSerializer
    lookup_url_kwarg = ["course_code", "class_code"]
    lookup_field = ["class_code", "course__course_code"]

    def get_object(self):
        course_code = self.kwargs.get("course_code")
        class_code = self.kwargs.get("class_code")
        obj = get_object_or_404(
            Class.objects.filter(course__course_code=course_code).select_related(
                "course"
            ),
            class_code=class_code,
        )
        self.check_object_permissions(self.request, obj)
        return obj


# class CourseTeacherList(generics.ListCreateAPIView):
#     permission_classes = [IsAuthenticated, CanManageCourseData]
#     lookup_url_kwarg = ["course_code"]
#     serializer_class = CourseTeacherSerializer

#     # def check_permissions(self):
#     #     return (
#     #         CourseTeacher.objects.filter(
#     #             course=self.kwargs.get("course_code"), teacher=self.request.user
#     #         )
#     #         .select_related("teacher")
#     #         .exists()
#     #     )

#     def get_queryset(self):
#         return CourseTeacher.objects.filter(
#             course__course_code=self.kwargs.get("course_code")
#         ).prefetch_related("course_semester")

#     def perform_create(self, serializer):
#         target_course = Course.objects.get(course_code=self.kwargs.get("course_code"))
#         serializer.save(course=target_course)


# class CourseTeacherDetail(generics.RetrieveUpdateDestroyAPIView):
#     permission_classes = [IsAuthenticated, CanManageCourseData]
#     lookup_url_kwarg = ["pk", "course_code"]
#     lookup_field = ["pk", "course__course_code"]
#     serializer_class = CourseTeacherSerializer

#     def get_object(self):
#         course_code = self.kwargs.get("course_code")
#         pk = self.kwargs.get("pk")

#         queryset = CourseTeacher.objects.filter(
#             course__course_code=course_code
#         ).prefetch_related("course_semester")
#         if not queryset.exists():
#             raise exceptions.NotFound("The requested course does not exist")
#         obj = get_object_or_404(queryset, pk=pk)
#         self.check_object_permissions(self.request, obj)
#         return obj


class LabList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LabSerializer

    def get_queryset(self):
        course_code = self.kwargs.get("course_code")
        class_code = self.kwargs.get("class_code")
        try:
            target_class = Class.objects.get(class_code=class_code)
            if target_class.course.course_code != course_code:
                raise serializers.ValidationError({"Class": "Unmatch Course & Class"})
        except Class.DoesNotExist as e:
            raise serializers.ValidationError({"Class": [str(e)]})
        return Lab.objects.filter(
            class_code__course__course_code=course_code,
            class_code__class_code=class_code,
        ).select_related("class_code")

    def perform_create(self, serializer):
        class_code = self.kwargs.get("class_code")
        try:
            target_class = Class.objects.get(class_code=class_code)
            serializer.save(class_code=target_class)
        except Class.DoesNotExist as e:
            raise serializers.ValidationError({"Class": [str(e)]})


class LabDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LabSerializer
    queryset = Lab.objects.all()
    lookup_url_kwarg = ["class_code", "course_code", "lab_name"]
    lookup_field = ["class_code", "course_code", "lab_name"]

    def get_object(self):
        course_code = self.kwargs.get("course_code")
        class_code = self.kwargs.get("class_code")
        lab_name = self.kwargs.get("lab_name")
        queryset = self.get_queryset()
        obj = get_object_or_404(
            queryset,
            class_code__course__course_code=course_code,
            class_code__class_code=class_code,
            lab_name=lab_name,
        )
        self.check_object_permissions(self.request, obj)
        return obj


class LearningOutcomeList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
    serializer_class = LabLOContributionSerializer
    lookup_url_kwarg = ["class_code", "course_code", "lab_name"]
    lookup_field = ["class_code", "course_code", "lab_name"]

    def get_queryset(self):
        course_code = self.kwargs.get("course_code")
        class_code = self.kwargs.get("class_code")
        return LabLOContribution.objects.filter(
            class_code__class_code=class_code,
            class_code__course__course_code=course_code,
            lab__lab_name=lab_name,
        ).select_related("class_code", "lab")

    def perform_create(self, serializer):
        course_code = self.kwargs.get("course_code")
        class_code = self.kwargs.get("class_code")
        lab_name = self.kwargs.get("lab_name")
        try:
            target_lab = Lab.objects.get(
                class_code__class_code=class_code,
                class_code__course__course_code=course_code,
                lab_name=lab_name,
            )
        except Lab.DoesNotExist as e:
            raise serializers.ValidationError({"Lab": [str(e)]})

        serializer.save(
            lab=target_lab,
            class_code=target_lab.class_code,
        )


class LabLODetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LabLOContributionSerializer
    lookup_url_kwarg = ["class_code", "course_code", "lab_name", "outcome_code"]
    lookup_field = ["class_code", "course_code", "lab_name", "outcome_code"]

    def get_object(self):
        course_code = self.kwargs.get("course_code")
        class_code = self.kwargs.get("class_code")
        lab_name = self.kwargs.get("lab_name")
        outcome_code = self.kwargs.get("outcome_code")
        obj = get_object_or_404(
            LabLOContribution.objects.filter(
                class_code__class_code=class_code,
                lab__lab_name=lab_name,
                class_code__course__course_code=course_code,
            ).select_related("class_code", "lab"),
            outcome__outcome_code=outcome_code,
        )
        self.check_object_permissions(self.request, obj)
        return obj
