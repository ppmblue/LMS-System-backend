from courses.models import (
    Course,
    Semester,
    Class,
    Lab,
    LearningOutcome,
    LabLOContribution,
    SubmissionData
)
from rest_framework import exceptions, serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from courses.permissions import CanAccessClass

from courses.serializers import (
    CourseSerializer,
    SemesterSerializer,
    ClassSerializer,
    LabSerializer,
    LearningOutcomeSerializer,
    LabLOContributionSerializer,
    SubmissionSerializer
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
        serializer.save(creator=self.request.user.email)


class CourseDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = CourseSerializer
    queryset = Course.objects.all()
    lookup_field = "course_code"

class ClassListByCourse(generics.ListCreateAPIView):
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
        
class ClassList(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTeacher, CanAccessClass]
    serializer_class = ClassSerializer
    
    def get_queryset(self):
        queryset = Class.objects.all()
        return queryset.filter(teacher__email=self.request.user.email)
    
    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user.email)


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
    

class SemesterList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SemesterSerializer
    
    def get_queryset(self):
        return Semester.objects.all()
    
    def perform_create(self, serializer):
        serializer.save()


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
        lab_name = self.kwargs.get("lab_name")
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

class SubmissionFile(ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SubmissionSerializer
    
    def create(self, request):
        serializer = SubmissionSerializer(data=request.data)
        file = request.FILES.get('submission_file')
        
        print('Request ', request.data, file.name)
        if (serializer.is_valid()):
            if not '.csv' in file.name:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            
            class_code = serializer.validated_data.get('class_code')
            try:
                target_class = Class.objects.get(
                    class_code = class_code
                )
            except Class.DoesNotExist as e:
                return Response(status.HTTP_400_BAD_REQUEST)
            
            serializer.save(
                class_code = target_class,
                binaries = file
            )
            
            # Process file
            self.processFile(file)
            
            return Response(f"Uploaded {file.name} successfully!")
            
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    def processFile(self, file):
        try: 
            file_data = file.read().decode('utf-8')
            lines = file_data.split('\r\n')
            
            submissions = []
            for line in lines[1:]:
                fields = line.split(',')
                if (len(fields) < 10): continue
                
                submit = SubmissionData()
                submit.last_name = fields[0]
                submit.first_name = fields[1]
                submit.student_id = self.get_integer_value(fields[2], 2012715)
                submit.started_time = fields[4]
                submit.end_time = fields[5]
                submit.grade = self.get_float_value(fields[7])
                submit.question_id = self.get_integer_value(fields[9], 0)
                submissions.append(submit)
                
            # Save into database
            print('Length ', len(submissions))
            SubmissionData.objects.bulk_create(submissions, batch_size=100)
            
        except Exception as e:
            raise e
        
    def get_integer_value(self, str, default_val):
        try:
            int_value = int(str)
            return int_value
        except (TypeError, ValueError):
            return default_val
        
    def get_float_value(self, str):
        try:
            float_val = float(str)
            return float_val
        except (TypeError, ValueError):
            return 0