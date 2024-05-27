from decimal import Decimal
from courses.models import (
    Course,
    Semester,
    Class,
    Lab,
    LearningOutcome,
    LabLOContribution,
    Exercise,
    Submission,
    OutcomeProgress,
    Enrollment
)
from students.models import Student
from rest_framework import serializers, status, parsers, generics, views
from rest_framework.response import Response
from courses.permissions import CanAccessClass
from courses.tasks import process_submission_file_task
from django.db.models import Sum, Avg

from courses.serializers import (
    CourseSerializer,
    SemesterSerializer,
    ClassSerializer,
    LabSerializer,
    LearningOutcomeSerializer,
    LabLOContributionSerializer,
    SubmissionFormSerializer,
    ExerciseFormSerializer,
    ExerciseSerializer,
    SubmissionSerializer,
    ExerciseAnalysisSerializer,
    LabLOContributionListSerializer
)
from students.serializers import StudentSerializer
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
            for y in ["PreLab", "InLab", "PostLab"]:
                weight_value = 0.2 if y == "PreLab" else 0.4
                lab = Lab(
                    lab_type=y,
                    lab_name=f"{x}-{y.split('Lab')[0].lower()}",
                    class_code=new_class,
                    weight=weight_value,
                )
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
        

class EnrollClassList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = ["student_id"]
    serializer_class = ClassSerializer
    
    def get_queryset(self):
        student_id = int(self.kwargs.get("student_id"))
        enroll_classes = Enrollment.objects.filter(student__student_id=student_id).values_list('class_code__class_code', flat=True).distinct()
        
        return Class.objects.filter(class_code__in=enroll_classes)


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


class ExerciseList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExerciseSerializer
    lookup_url_kwarg = ["class_code"]

    def get_queryset(self):
        class_code = self.kwargs.get("class_code")

        return Exercise.objects.filter(class_code=class_code)

    def perform_create(self, serializer):
        target_course = self.kwargs.get("class_code")
        serializer.save(class_code=target_course)


class ExerciseDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExerciseSerializer
    lookup_url_kwarg = ["class_code", "exercise_id"]

    def get_object(self):
        obj = get_object_or_404(
            Exercise.objects.all(),
            class_code=self.kwargs.get("class_code"),
            exercise_id=int(self.kwargs.get("exercise_id")),
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
    
class LOContributionSummarize(views.APIView):
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = ["course_code", "class_code"]
    
    def get(self, request, *args, **kwargs):
        course_code = self.kwargs.get("course_code")
        class_code = self.kwargs.get("class_code")
        try:
            target_class = Class.objects.get(class_code=class_code, course__course_code=course_code)
        except Class.DoesNotExist as e:
            return Response(status.HTTP_400_BAD_REQUEST)
        num_of_labs = target_class.num_of_lab
        result = []
        for outcome in LearningOutcome.objects.all():
            result.append({
                'parent_outcome': outcome.parent_outcome,
                'outcome_code': outcome.outcome_code,
                'threshold': outcome.threshold,
                'labs': [-1 for x in range(0, num_of_labs)]
            })
            
        # Check available or absent contribution
        for item in result:
            for x in range(0, num_of_labs):
                lab = x + 1
                if Exercise.objects.filter(outcome__outcome_code=item['outcome_code'],
                    lab__lab_name__contains=f'{lab}').exists():
                    item['labs'][x] = 0
                    
        # Calculate existing contribution
        for item in result:
            for x in range(0, num_of_labs):
                if (item['labs'][x] < 0): continue
                
                lab = x + 1
                contribution = LabLOContribution.objects.filter(outcome__outcome_code=item['outcome_code'],
                    class_code__class_code=class_code,
                    lab__lab_name__contains=f'{lab}').aggregate(total = Sum('contribution_percentage'))['total']
                if contribution:
                    item['labs'][x] = contribution
                
        return Response(result)
    
    def post(self, request, *args, **kwargs):
        course_code = self.kwargs.get("course_code")
        class_code = self.kwargs.get("class_code")
        try:
            target_class = Class.objects.get(class_code=class_code, course__course_code=course_code)
        except Class.DoesNotExist as e:
            return Response(status.HTTP_400_BAD_REQUEST)
        
        serializer = LabLOContributionListSerializer(data=request.data, many=True)
        if serializer.is_valid():
            for item in serializer.data:
                labs = self.get_types_of_lab(class_code, item['outcome_code'], item['lab'])
                weights = [0.2, 0.4, 0.4] if len(labs) == 3 else [0.3, 0.7]
                outcome = LearningOutcome.objects.get(outcome_code=item['outcome_code'], course__course_code=course_code)
                for index, lab_val in enumerate(labs):
                    lab = Lab.objects.get(id=lab_val)
                    # If lab_lo_contribution is already created, let's update contribution value
                    if LabLOContribution.objects.filter(lab__id=lab.id, outcome__pk=outcome.pk).exists():
                        lo_contribution = LabLOContribution.objects.get(lab__id=lab.id, outcome__pk=outcome.pk)
                        lo_contribution.contribution_percentage = float(item['contribution'])*weights[index]
                        lo_contribution.save()
                    else:
                        LabLOContribution(lab=lab, outcome=outcome, class_code=target_class, contribution_percentage=float(item['contribution'])*weights[index]).save()
                
            return Response(serializer.data)
        
        return Response(status.HTTP_400_BAD_REQUEST)
        
    def get_types_of_lab(self, class_code, outcome, lab):
        return Exercise.objects.filter(
            class_code=class_code,
            outcome__outcome_code=outcome,
            lab__lab_name__contains=f'{lab}'
        ).values_list('lab__id', flat=True).distinct()
            
                  

class ExerciseUploadForm(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExerciseFormSerializer
    parser_classes = (parsers.MultiPartParser, parsers.FileUploadParser)

    def post(self, request, *args, **kwargs):
        serializer = ExerciseFormSerializer(data=request.data)
        file = request.FILES.get("exercise_file")

        print("Upload exercise file: ", request.data, file.name)
        if serializer.is_valid():
            if not ".csv" in file.name:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            class_code = serializer.validated_data.get("class_code")
            try:
                target_class = Class.objects.get(class_code=class_code)
            except Class.DoesNotExist as e:
                return Response(status.HTTP_400_BAD_REQUEST)

            # Process file
            self.processFile(target_class, file)

            return Response(f"Process exersise file {file.name} successfully!")

        return Response(status=status.HTTP_400_BAD_REQUEST)

    def processFile(self, target_class, file):
        try:
            file_data = file.read().decode("utf-8")
            lines = file_data.split("\r\n")

            exercises = []
            for line in lines[1:]:
                fields = line.split(";")
                if len(fields) != 8:
                    continue

                new_exercise_id = self.get_integer_value(str(fields[6]).split("id=")[1], 0)
                if Exercise.objects.filter(exercise_id=new_exercise_id, class_code=target_class.class_code).exists():
                    print('Duplicated exercise: ', new_exercise_id, target_class.class_code)
                    continue

                # Validate outcome. Create new outcome if not existed
                outcome_code = (
                    f"{fields[7]}.0" if len(str(fields[7])) <= 5 else str(fields[7])
                )
                course_code = target_class.course.course_code
                outcome = LearningOutcome()
                if not (
                    LearningOutcome.objects.filter(
                        outcome_code=outcome_code, course__course_code=course_code
                    ).exists()
                ):
                    outcome = LearningOutcome(
                        outcome_code=outcome_code, course=target_class.course
                    )
                    outcome.parent_outcome = outcome_code[0:5]
                    outcome.save()
                else:
                    outcome = LearningOutcome.objects.get(
                        outcome_code=outcome_code, course__course_code=course_code
                    )

                exercise = Exercise()
                exercise.exercise_id = self.get_integer_value(str(fields[6]).split("id=")[1], 0)
                exercise.exercise_code = fields[2]
                exercise.exercise_name = str(fields[3]).split("]")[1].strip()
                exercise.url = fields[6]
                exercise.outcome = outcome
                exercise.lab = Lab.objects.get(
                    lab_name=f"{fields[0]}-{str(fields[1]).split('lab')[0].lower()}",
                    class_code__id=target_class.id    
                )
                exercise.class_code = target_class.class_code
                exercise.course_code = target_class.course.course_code
                exercise.topic = fields[4]
                exercise.level = self.get_integer_value(str(fields[5]).split("-")[0], 0)
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
        
class ExersiceContributionAnalysis(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExerciseAnalysisSerializer
    parser_classes = (parsers.MultiPartParser, parsers.FileUploadParser)
    lookup_url_kwarg = ["course_code"]
    
    def post(self, request, *args, **kwargs):
        serializer = ExerciseAnalysisSerializer(data=request.data)
        file = request.FILES.get("exercise_file")
        course_code = self.kwargs.get("course_code")
        
        print("Upload exercise file: ", request.data, file.name)
        result = []
        if serializer.is_valid():
            if not ".csv" in file.name:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            
            # Analyze absent/available of lab-outcome
            file_data = file.read().decode("utf-8")
            lines = file_data.split("\r\n")
            for line in lines[1:]:
                fields = line.split(";")
                if len(fields) != 8: continue
            
                # Validate outcome. Create new outcome if not existed
                outcome_code = (
                    f"{fields[7]}.0" if len(str(fields[7])) <= 5 else str(fields[7])
                )
                outcome = LearningOutcome.objects.get(
                    outcome_code=outcome_code, course__course_code=course_code
                )
                lab = f'Lab {fields[0]}'
                if len(result) == 0:
                    result.append({
                        'outcome_code': outcome.outcome_code,
                        'threshold': outcome.threshold,
                        'labs': [lab]
                    })
                elif not any(x['outcome_code'] == outcome.outcome_code for x in result):
                    result.append({
                        'outcome_code': outcome.outcome_code,
                        'threshold': outcome.threshold,
                        'labs': [lab]
                    })
                else:
                    if not any(x['outcome_code'] == outcome.outcome_code and lab in x['labs'] for x in result):
                        for item in result:
                            if item['outcome_code'] == outcome.outcome_code:
                                item['labs'].append(lab)

            return Response(result)
        
        return Response(status=status.HTTP_400_BAD_REQUEST)
                
    

class SubmissionUploadForm(views.APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubmissionFormSerializer
    parser_classes = (parsers.MultiPartParser, parsers.FileUploadParser)
    
    def post(self, request, *args, **kwargs):
        serializer = SubmissionFormSerializer(data=request.data)
        file = request.FILES.get("submission_file")

        print("Upload submission file: ", request.data, file.name)
        if serializer.is_valid():
            if not ".csv" in file.name:
                return Response(status=status.HTTP_400_BAD_REQUEST)

            class_code = serializer.validated_data.get("class_code")
            try:
                target_class = Class.objects.get(class_code=class_code)
                target_class.num_submit_file += 1
                target_class.save()
            except Class.DoesNotExist as e:
                return Response(status.HTTP_400_BAD_REQUEST)

            # Save file in storage
            new_file = serializer.save(class_code=target_class, binaries=file)

            # Process file
            process_submission_file_task.apply_async(
                args=[target_class.class_code, file.name, new_file.id]
            )

            return Response(f"Uploaded submission file {file.name} successfully!")

        return Response(status=status.HTTP_400_BAD_REQUEST)


class SubmissionList(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubmissionSerializer
    lookup_url_kwarg = ["class_code"]

    def get_queryset(self):
        class_code = self.kwargs.get("class_code")
        page = self.request.query_params.get("page")
        items = self.request.query_params.get("items")
        sortBy = self.request.query_params.get("sortBy")
        sortOrder = self.request.query_params.get("sortOrder")

        submissions = Submission.objects.all()
        if sortBy and sortOrder:
            if sortOrder == 'desc':
                submissions = submissions.order_by(f'-{sortBy}')
            else:
                submissions = submissions.order_by(sortBy)

        if page and items:
            num_page = int(page)
            if num_page == 1:
                return submissions.filter(exercise__class_code=class_code)[
                    : (int(page) * int(items))
                ]

            return submissions.filter(exercise__class_code=class_code)[
                ((num_page - 1) * int(items)) : (num_page * int(items))
            ]

        return submissions.filter(exercise__class_code=class_code)[:100]

class OutcomeProgressAnalysisList(views.APIView):
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = ["student_id", "class_code", "start_lab", "end_lab"]
    
    def get(self, request, *args, **kwargs):
        student_id = self.kwargs.get("student_id")
        class_code = self.kwargs.get("class_code")
        start_lab = self.kwargs.get("start_lab")
        end_lab = self.kwargs.get("end_lab")
        
        try:
            target_class = Class.objects.get(class_code=class_code)
        except Exception:
            return Response(status.HTTP_400_BAD_REQUEST)
        
        if student_id == 'all':
            page = self.request.query_params.get("page")
            items = self.request.query_params.get("items")
            query = self.request.query_params.get("query")
            
            result = []
            student_ids = Enrollment.objects.filter(class_code__class_code=class_code).values_list('student__student_id', flat=True).distinct()
            
            if query and query != '':
                student_ids = list(filter(lambda x: query in f'{x}', student_ids))
            
            if page and items:
                num_page = int(page)
                num_items = int(items)
                if num_page == 1:
                    student_ids = student_ids[:num_page * num_items]
                else:
                    student_ids = student_ids[(num_page - 1) * num_items : num_page * num_items]
            
            for student in Student.objects.filter(student_id__in=student_ids):
                item = self.get_outcome_progress(student, start_lab, end_lab, target_class, False)
                result.append(item)
                
            return Response(result)

        else:
            try:
                student = Student.objects.get(student_id=int(student_id))
            except Exception:
                return Response(status.HTTP_400_BAD_REQUEST)
            
            return Response(self.get_outcome_progress(student, start_lab, end_lab, target_class, True))
    
    def get_outcome_progress(self, student, start_lab, end_lab, target_class, checkProgress):
        # Find outcome progress for one student
        result = {}
        result['student'] = student.student_id
        result['first_name'] = student.first_name
        result['last_name'] = student.last_name
        result['secured_student'] = student.secured_student_id
        lab_names = self.get_interval(start_lab, end_lab, target_class.num_of_lab) if checkProgress else [start_lab, end_lab]
        # Init value
        for outcome in LearningOutcome.objects.all():
            result[f'{outcome.outcome_code}'] = []
            result[f'max_{outcome.outcome_code}'] = []
                
        # Calculate outcome progress through start lab -> end lab
        for lab_name in lab_names:
            progress_vals = OutcomeProgress.objects.filter(lab__lab_name=lab_name
                , lab__class_code__class_code=target_class.class_code
                , student__student_id=student.student_id)
        
            for progress in progress_vals:
                result[f'{progress.outcome.outcome_code}'].append(progress.progress)
                result[f'max_{progress.outcome.outcome_code}'].append(progress.max_progress)
        
        return result
            
            
    # Calculate interval between 2 labs
    def get_interval(self, start_lab, end_lab, num_of_lab):
        matrix = [[f'{x}-pre', f'{x}-in', f'{x}-post'] for x in range(1, num_of_lab + 1)]
        all_labs = [item for row in matrix for item in row]
        
        # Calculate index
        start_idx = all_labs.index(start_lab)
        end_idx = all_labs.index(end_lab) + 1
        labs = all_labs[start_idx : end_idx]
        
        return labs


class OutcomeProgressSummarizeByLab(views.APIView):
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = ["class_code", "lab_name"]
    
    def get(self, request, *args, **kwargs):
        class_code = self.kwargs.get("class_code")
        lab_name = self.kwargs.get("lab_name")
        
        try:
            target_class = Class.objects.get(class_code=class_code)
            lab = Lab.objects.get(lab_name=lab_name, class_code__class_code=class_code)
        except Exception:
            return Response(status.HTTP_400_BAD_REQUEST)
        
        outcomes = LearningOutcome.objects.filter(course__course_code=target_class.course.course_code)
        total_students = Enrollment.objects.filter(class_code__class_code=class_code).values_list('student__student_id', flat=True).distinct().count()
        passed = []
        failed = []
        for outcome in outcomes:
            curr_passed = OutcomeProgress.objects.filter(lab=lab, outcome=outcome, progress__gte=0.5).count()
            curr_failed = OutcomeProgress.objects.filter(lab=lab, outcome=outcome, progress__lt=0.5).count()
            
            passed.append(curr_passed)
            failed.append(curr_failed)
            
        return Response({
            "total_students": total_students,
            "passed": passed,
            "failed": failed,
            "outcomes": outcomes.values_list('outcome_code', flat=True)
        })
        
class OutcomeProgressSummarizeDetail(views.APIView):
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = ["class_code", "outcome_code"]
    
    def get(self, request, *args, **kwargs):
        class_code = self.kwargs.get("class_code")
        outcome_code = self.kwargs.get("outcome_code")
        try:
            target_class = Class.objects.get(class_code=class_code)
            outcome=LearningOutcome.objects.get(outcome_code=outcome_code, course__course_code=target_class.course.course_code)
        except Class.DoesNotExist as e:
            return Response(status.HTTP_400_BAD_REQUEST)

        result = {
            "outcome_code": outcome.outcome_code,
            "threshold": outcome.threshold,
            "labs": []
        }
                    
        # Calculate lab contributions
        for contribution in LabLOContribution.objects.filter(outcome=outcome, class_code=target_class):
            result["labs"].append({
                "lab": contribution.lab.lab_name,
                "contribution": contribution.contribution_percentage
            })
            
        # Calculate pass/fail rate
        last_lab = Lab.objects.get(class_code=target_class, lab_name=f'{target_class.num_of_lab}-post')
        result["passed"] = OutcomeProgress.objects.filter(lab=last_lab, outcome=outcome, progress__gte=0.5).count()
        result["failed"] = OutcomeProgress.objects.filter(lab=last_lab, outcome=outcome, progress__lt=0.5).count()
        result["rate"] = round(result["passed"] / (result["passed"] + result["failed"]), 2) if (result["passed"] + result["failed"]) > 0 else 0
                
        return Response(result)
    
class OutcomeProgressHistogram(views.APIView):
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = ["class_code", "outcome_code"]
    
    def get(self, request, *args, **kwargs):
        class_code = self.kwargs.get("class_code")
        outcome_code = self.kwargs.get("outcome_code")
        try:
            target_class = Class.objects.get(class_code=class_code)
            outcome=LearningOutcome.objects.get(outcome_code=outcome_code, course__course_code=target_class.course.course_code)
        except Class.DoesNotExist as e:
            return Response(status.HTTP_400_BAD_REQUEST)

        result = {
            "outcome_code": outcome.outcome_code
        }
            
        # Calculate pass/fail rate
        last_lab = Lab.objects.get(class_code=target_class, lab_name=f'{target_class.num_of_lab}-post')
        result["0 - 0.2"] = OutcomeProgress.objects.filter(lab=last_lab, outcome=outcome, progress__lt=0.2).count()
        result["0.2 - 0.4"] = OutcomeProgress.objects.filter(lab=last_lab, outcome=outcome, progress__lt=0.4, progress__gte=0.2).count()
        result["0.4 - 0.6"] = OutcomeProgress.objects.filter(lab=last_lab, outcome=outcome, progress__lt=0.6, progress__gte=0.4).count()
        result["0.6 - 0.8"] = OutcomeProgress.objects.filter(lab=last_lab, outcome=outcome, progress__lt=0.8, progress__gte=0.6).count()
        result["0.8 - 1"] = OutcomeProgress.objects.filter(lab=last_lab, outcome=outcome, progress__gte=0.8).count()
        result["average"] = round(OutcomeProgress.objects.filter(lab=last_lab, outcome=outcome).aggregate(avg = Avg('progress'))['avg'], 2)
                
        return Response(result)
    
class StudentListByClass(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StudentSerializer
    lookup_url_kwarg = ["class_code"]

    def get_queryset(self):
        class_code = self.kwargs.get("class_code")
        
        try:
            _ = Class.objects.get(class_code=class_code)
        except Exception:
            return Response(status.HTTP_400_BAD_REQUEST)
        student_ids = Enrollment.objects.filter(class_code__class_code=class_code).values_list('student__student_id', flat=True).distinct()
        
        return Student.objects.filter(
            student_id__in=student_ids
        )
        
class ExerciseRecommendation(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExerciseSerializer
    lookup_url_kwarg = ["class_code", "student_id"]

    def get_queryset(self):
        class_code = self.kwargs.get("class_code")
        student_id = self.kwargs.get("student_id")
        
        try:
            _ = Class.objects.get(class_code=class_code)
        except Exception:
            return Response(status.HTTP_400_BAD_REQUEST)
        
        return Exercise.objects.filter(
            class_code = class_code
        )[:5]