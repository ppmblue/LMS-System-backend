from django.db import models
from user_profiles.models import UserProfile
from django.core.validators import MaxValueValidator, MinValueValidator


class Course(models.Model):
    course_name = models.CharField(max_length=255)
    department = models.CharField(max_length=100)

    creater = models.ForeignKey(
        UserProfile,
        related_name="teacher_create_course",
        on_delete=models.RESTRICT,
        null=True,
    )

    def __str__(self):
        return self.course_name


class CourseSemester(models.Model):
    semester_name = models.CharField(max_length=50)
    course = models.ForeignKey(
        Course, related_name="course_semester", on_delete=models.CASCADE
    )
    num_of_lab = models.IntegerField()

    def __str__(self):
        return self.semester_name


class Lab(models.Model):
    LAB_TYPE_CHOICES = [
        ("PreLab", "Pre Lab"),
        ("InLab", "In Lab"),
        ("PostLab", "Post Lab"),
    ]
    weight = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)], null=True
    )
    lab_name = models.CharField(primary_key=True, blank=True, unique=True)
    lab_type = models.CharField(max_length=50, choices=LAB_TYPE_CHOICES)

    course_semester = models.ForeignKey(
        CourseSemester, on_delete=models.CASCADE, null=True
    )

    def save(self, *args, **kwargs):
        if not self.lab_name:
            last_lab = Lab.objects.order_by("-lab_name").first()
            if last_lab:
                lab_number = int(last_lab.lab_name.split("-")[0].replace("Lab", "")) + 1
            else:
                lab_number = 1
            self.lab_name = f"Lab{lab_number}-{self.lab_type}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Lab {self.lab_name}"


class LearningOutcome(models.Model):
    outcome_name = models.CharField(max_length=255)
    outcome_description = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.outcome_name


class LabLOContribution(models.Model):
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE, null=True)
    learning_outcome = models.ForeignKey(
        LearningOutcome, on_delete=models.CASCADE, null=True
    )
    contribution_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    course_semester = models.ForeignKey(
        CourseSemester, on_delete=models.CASCADE, null=True
    )

    def __str__(self):
        return f"{self.lab.lab_name} - {self.learning_outcome.outcome_description} - {self.course_semester.semester_name}"


class CourseTeacher(models.Model):
    TEACHER_ROLE_CHOICES = [
        ("Lecturer", "Lecturer"),
        ("HeadLecturer", "Head Lecturer"),
        ("TA", "Teaching Assistant"),
    ]
    role = models.CharField(max_length=100, choices=TEACHER_ROLE_CHOICES)
    teacher = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True)
    course_semester = models.ManyToManyField(
        CourseSemester, related_name="semester_teacher"
    )

    def __str__(self):
        return f"{self.course_semester} - {self.teacher.first_name} -{self.role}"
