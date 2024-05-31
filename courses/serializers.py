from rest_framework import serializers
from courses.models import (
    Course,
    Class,
    Lab,
    Semester,
    LearningOutcome,
    LabLOContribution,
    UploadForm,
    Exercise,
    Submission,
    Enrollment
)
from user_profiles.models import UserProfile
from students.models import Student


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "pk",
            "course_code",
            "course_name",
            "department",
            "creator",
        ]
        read_only_fields = ["creator"]
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
    
    num_of_submissions = serializers.SerializerMethodField('count_submissions')
    num_of_exercises = serializers.SerializerMethodField('count_exercises')
    num_of_outcomes = serializers.SerializerMethodField('count_outcomes')
    num_of_students = serializers.SerializerMethodField('count_students')
    
    def count_submissions(self, obj):
        return Submission.objects.filter(exercise__class_code=obj.class_code).count()
    
    def count_exercises(self, obj):
        return Exercise.objects.filter(class_code=obj.class_code).count()
    
    def count_outcomes(self, obj):
        return LearningOutcome.objects.filter(course__course_code=obj.course.course_code).values('parent_outcome').distinct().count()
    
    def count_students(self, obj):
        return Enrollment.objects.filter(class_code__class_code=obj.class_code).count()

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
            "num_of_submissions",
            "num_of_exercises",
            "num_submit_file",
            "num_of_outcomes",
            "num_of_students"
        )
        lookup_field = ["course", "class_code"]
        read_only_fields = ["class_code"]


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
        
class LearningOutcomeListSerializer(serializers.Serializer):
    outcome_code = serializers.CharField()
    outcome_description = serializers.CharField(allow_blank=True)
    threshold = serializers.IntegerField()
    parent_outcome = serializers.CharField()
    
    class Meta:
        fields = ['outcome_code', 'outcome_description', 'threshold', 'parent_outcome']


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

class LabLOContributionListSerializer(serializers.Serializer):
    outcome_code = serializers.CharField()
    lab = serializers.IntegerField()
    contribution = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        fields = ['outcome_code', 'lab', 'contribution']


class SubmissionFormSerializer(serializers.ModelSerializer):
    submission_file = serializers.FileField(source='binaries')
    
    class Meta:
        model = UploadForm
        fields = ['class_code', 'submission_file']
        
class ExerciseFormSerializer(serializers.ModelSerializer):
    exercise_file = serializers.FileField(source='binaries')
    
    class Meta:
        model = UploadForm
        fields = ['class_code', 'exercise_file']
        
class ExerciseAnalysisSerializer(serializers.ModelSerializer):
    exercise_file = serializers.FileField(source='binaries')
    
    class Meta:
        model = UploadForm
        fields = ['exercise_file']
        
class ExerciseSerializer(serializers.ModelSerializer):
    lab = serializers.SlugRelatedField(
        queryset=Lab.objects.filter(),
        slug_field='lab_name'
    )
    outcome = serializers.SlugRelatedField(
        queryset=LearningOutcome.objects.filter(),
        slug_field='outcome_code'
    )
        
    class Meta:
        model = Exercise
        fields = ['id', 'exercise_id', 'exercise_code', 'exercise_name', 'class_code', 'level', 'topic', 'lab', 'outcome', 'url']
        
class CreateExerciseSerializer(serializers.ModelSerializer):   
    class Meta:
        model = Exercise
        fields = ['id', 'exercise_id', 'exercise_code', 'exercise_name', 'level', 'topic', 'outcome', 'url']
        
class SubmissionSerializer(serializers.ModelSerializer):
    exercise = serializers.SlugRelatedField(
        queryset=Exercise.objects.filter(),
        slug_field='exercise_id'
    )
    student = serializers.SlugRelatedField(
        queryset=Student.objects.filter(),
        slug_field='secured_student_id'
    )
    started_time = serializers.SerializerMethodField('get_format_starttime')
    submitted_time = serializers.SerializerMethodField('get_format_endtime')
    time_taken = serializers.SerializerMethodField('get_format_duration')
    
    def get_format_starttime(self, obj):
        return obj.started_time.strftime("%d/%m/%Y, %H:%M:%S")
    
    def get_format_endtime(self, obj):
        return obj.started_time.strftime("%d/%m/%Y, %H:%M:%S")
    
    def get_format_duration(self, obj):
        days = obj.time_taken.days
        seconds = obj.time_taken.seconds

        minutes = seconds // 60

        hours = minutes // 60
        hour_str = f'{hours} hours' if hours > 1 else '1 hour' if hours == 1 else ''
        minutes = minutes % 60
        min_str = f'{minutes} mins' if minutes > 1 else '1 min' if minutes == 1 else '0 min'

        dur_string = f'{hour_str} {min_str}' if hour_str != '' else min_str
        if days:
            day_str = 'days' if days > 1 else 'day'
            dur_string = f'{days} {day_str} {dur_string}'
        return dur_string
    
    class Meta:
        model = Submission
        fields = ['exercise', 'student', 'score', 'time_taken', 'started_time', 'submitted_time']