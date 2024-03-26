from django.db import models
from user_profiles.models import UserProfile
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator

# from django.core.validators import MinValueValidator, MaxValueValidator


class Course(models.Model):
    id = models.AutoField(primary_key=True)
    course_code = models.CharField(max_length=50, unique=True, null=True)
    course_name = models.CharField(max_length=255)
    department = models.CharField(max_length=100)
    creater = models.EmailField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=["course_name"]),
        ]

    def __str__(self):
        return f"{self.course_code}-{self.course_name}"


class Semester(models.Model):
    id = models.AutoField(primary_key=True)
    semester_name = models.CharField(
        max_length=50,
        unique=True,
        validators=[
            RegexValidator(
                regex="^HK[0-9]+$",
                message="Semester must follow the format HK***",
                code="invalid_semestername",
            ),
        ],
    )

    def __str__(self):
        return f"{self.semester_name}"


class Class(models.Model):
    id = models.AutoField(primary_key=True)
    class_code = models.CharField(max_length=50, unique=True)
    semester = models.ForeignKey(
        Semester, related_name="class_semester", on_delete=models.SET_NULL, null=True
    )
    course = models.ForeignKey(
        Course, related_name="class_course", on_delete=models.CASCADE
    )
    group = models.CharField(max_length=50, null=True)
    num_of_lab = models.IntegerField()
    TEACHER_ROLE_CHOICES = [
        ("Lecturer", "Lecturer"),
        ("HeadLecturer", "Head Lecturer"),
        ("TA", "Teaching Assistant"),
    ]
    role = models.CharField(max_length=100, choices=TEACHER_ROLE_CHOICES)
    teacher = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True)

    def __str__(self):
        return f"{self.class_code}"

    def save(self, *args, **kwargs):
        if not self.class_code:
            semester_name = self.semester.semester_name
            semester_name = semester_name.replace("HK", "20")
            self.class_code = f"{semester_name}_{self.course.course_code}_{self.group}"

        super().save(*args, **kwargs)


class Lab(models.Model):
    id = models.AutoField(primary_key=True)
    LAB_TYPE_CHOICES = [
        ("PreLab", "Pre Lab"),
        ("InLab", "In Lab"),
        ("PostLab", "Post Lab"),
    ]
    weight = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    lab_name = models.CharField(max_length=50, unique=True)
    lab_type = models.CharField(max_length=50, choices=LAB_TYPE_CHOICES, null=True)
    class_code = models.ForeignKey(
        Class, related_name="lab_class", on_delete=models.CASCADE
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
    parent_outcome = models.CharField(max_length=255, blank=True)
    outcome_code = models.CharField(max_length=50)
    outcome_name = models.CharField(max_length=255)
    outcome_description = models.CharField(max_length=255, blank=True)
    threshold = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)], default=5
    )
    course = models.ForeignKey(
        Course, related_name="outcome_course", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.outcome_code}-{self.outcome_name}"


class LabLOContribution(models.Model):
    lab = models.ForeignKey(
        Lab, related_name="contribution_lab", on_delete=models.CASCADE
    )
    outcome = models.ForeignKey(
        LearningOutcome,
        related_name="contribution_lo",
        on_delete=models.CASCADE,
        null=True,
    )
    contribution_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=False
    )
    class_code = models.ForeignKey(
        Class, related_name="contribution_class", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.outcome.outcome_code}-{self.contribution_percentage} of {self.lab.lab_name}"


# class CourseTeacher(models.Model):
#     course = models.ForeignKey(
#         Course,
#         on_delete=models.CASCADE,
#         related_name="courseteacher_course",
#         blank=True,
#     )
#     TEACHER_ROLE_CHOICES = [
#         ("Lecturer", "Lecturer"),
#         ("HeadLecturer", "Head Lecturer"),
#         ("TA", "Teaching Assistant"),
#     ]
#     role = models.CharField(max_length=100, choices=TEACHER_ROLE_CHOICES)
#     teacher = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True)
#     # course_semester = models.ManyToManyField(
#     #     CourseSemester, related_name="courseteacher_semester"
#     # )

#     def __str__(self):
#         return f"{self.teacher.first_name} -{self.role}"
