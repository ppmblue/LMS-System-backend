from courses.models import (
    Course,
    Semester,
    Class,
    Lab,
    LearningOutcome,
    LabLOContribution,
    Exercise,
    Submission
)
from students.models import Student
from rest_framework import exceptions, serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from courses.permissions import CanAccessClass
from datetime import datetime, timedelta
import base64

from courses.serializers import (
    CourseSerializer,
    SemesterSerializer,
    ClassSerializer,
    LabSerializer,
    LearningOutcomeSerializer,
    LabLOContributionSerializer,
    SubmissionFormSerializer,
    ExerciseFormSerializer
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
        new_class = serializer.save(
            course=Course.objects.get(course_code=self.kwargs.get("course_code"))
        )
        
        # Auto generate labs based on num_of_lab
        labs = []
        for x in range(1, new_class.num_of_lab + 1):
            for y in ['PreLab', 'InLab', 'PostLab']:
                weight_value = 0.2 if y == 'PreLab' else 0.4
                lab = Lab(lab_type=y, lab_name=f"{x}-{y.split('Lab')[0].lower()}", class_code=new_class, weight=weight_value)
                labs.append(lab)
                
        Lab.objects.bulk_create(labs)
        
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
    
class ExerciseUploadForm(ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ExerciseFormSerializer
    
    def create(self, request):
        serializer = ExerciseFormSerializer(data=request.data)
        file = request.FILES.get('exercise_file')
        
        print('Upload exercise file: ', request.data, file.name)
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
            
            # Process file
            self.processFile(target_class, file)
            
            return Response(f"Process exersise file {file.name} successfully!")
        
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    def processFile(self, target_class, file):
        try: 
            file_data = file.read().decode('utf-8')
            lines = file_data.split('\r\n')
            
            exercises = []
            for line in lines[1:]:
                fields = line.split(';')
                print('Question fields: ', line, len(fields))
                if (len(fields) != 8): continue
                
                new_id = self.get_integer_value(str(fields[6]).split('id=')[1], 0)
                if Exercise.objects.filter(id=new_id).exists():
                    continue
                
                exercise = Exercise()
                exercise.id = self.get_integer_value(str(fields[6]).split('id=')[1], 0)
                exercise.exercise_code = fields[2]
                exercise.exercise_name = str(fields[3]).split(']')[1].strip()
                exercise.url = fields[6]
                exercise.outcome = f"{fields[7]}.0" if len(str(fields[7])) <= 5 else str(fields[7])
                exercise.lab_name = Lab.objects.get(lab_name=f"{fields[0]}-{str(fields[1]).split('lab')[0].lower()}")
                exercise.class_code = target_class.class_code
                exercise.course_code = target_class.course.course_code
                exercise.topic = fields[4]
                exercise.level = self.get_integer_value(str(fields[5]).split('-')[0], 0)
                exercises.append(exercise)
                
            # Save into database
            Exercise.objects.bulk_create(exercises, batch_size=100)
            
        except Exception as e:
            raise e
        
    def get_integer_value(self, str, default_val):
        try:
            int_value = int(str)
            return int_value
        except (TypeError, ValueError):
            return default_val
            

class SubmissionUploadForm(ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SubmissionFormSerializer
    
    def create(self, request):
        serializer = SubmissionFormSerializer(data=request.data)
        file = request.FILES.get('submission_file')
        
        print('Upload submission file: ', request.data, file.name)
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
            
            # Process file
            self.processFile(target_class, file)
            
            return Response(f"Uploaded submission file {file.name} successfully!")
            
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    def processFile(self, target_class, file):
        try: 
            file_data = file.read().decode('utf-8')
            lines = file_data.split('\r\n')
            
            submissions = []
            for line in lines[1:]:
                fields = line.split(',')
                if (len(fields) != 10): continue
                
                # Validate student. Create new student if not existed
                student_id = self.get_integer_value(fields[2], 2012715)
                student = Student()
                if not (Student.objects.filter(student_id=student_id).exists()):
                    student = Student(student_id=student_id)
                    student.last_name = fields[0]
                    student.first_name = fields[1]
                    student.secured_student_id = base64.urlsafe_b64encode(str(student_id).encode())
                    student.save()
                else:
                    student = Student.objects.get(student_id=student_id)
                    
                # Validate exercise. Create new exercise if not existed
                question_id = self.get_integer_value(fields[9], 0)
                exercise = Exercise()
                if not (Exercise.objects.filter(id=question_id).exists()):
                    exercise = Exercise(id=question_id, class_code=target_class.class_code)
                    exercise.save()
                else:
                    exercise = Exercise.objects.get(id=question_id)
                    
                submit = Submission()
                submit.student = student
                submit.exercise = exercise
                submit.score = self.get_float_value(fields[7])
                submit.time_taken = self.calculateTime(str(fields[6]))
                submit.started_time = self.convertDate(str(fields[4]))
                submit.submitted_time = self.convertDate(str(fields[5]))
                submissions.append(submit)
                
            # Save into database
            print('Length ', len(submissions))
            Submission.objects.bulk_create(submissions, batch_size=100)
            
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
        
    # Convert month
    def convertMonth(self, month):
        map = { "January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06",
                "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12" }
        for x in map.keys():
            month = month.replace(x, map[x])
        return month

    # Convert date
    def convertDate(self, date_str):
        date_str = self.convertMonth(date_str)
        date_format = '%d %m %Y %I:%M %p'

        date_obj = datetime.strptime(date_str, date_format)
        return date_obj
    
    # Convert 'Time taken' to timedelta
    def calculateTime(self, time):
        temp = time.split(' ')
        result = {
            'day': 0,
            'hour': 0,
            'min': 0,
            'sec': 0
        }
        for x in range(1, len(temp), 2):
            typ = temp[x]
            if 'day' in typ:
                result['day'] = int(temp[x-1])
            elif 'hour' in typ:
                result['hour'] = int(temp[x-1])
            elif 'min' in typ:
                result['min'] = int(temp[x-1])
            else:
                result['sec'] = int(temp[x-1])
        return timedelta(days=result['day'], hours=result['hour'], minutes=result['min'], seconds=result['sec'])