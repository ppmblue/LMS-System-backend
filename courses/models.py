from django.db import models


class Course(models.Model):
    course_name = models.CharField(max_length=255)
    department = models.CharField(max_length=100)
    num_of_lab = models.IntegerField()

    def __str__(self):
        return self.course_name

    
class Lab(models.Model):
    LAB_TYPE_CHOICES = [
        ('PreLab', 'Pre Lab'),
        ('InLab', 'In Lab'),
        ('PostLab', 'Post Lab'),
    ]

    lab_name = models.AutoField(primary_key=True)
    lab_type = models.CharField(max_length=50, choices=LAB_TYPE_CHOICES)
    weighted = models.BooleanField(default=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return f"Lab {self.lab_name}"


class Semester(models.Model):
    semester_name = models.CharField(max_length=50)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return self.semester_name

    
class LearningOutcome(models.Model):
    outcome_name = models.CharField(max_length=255)
    outcome_description = models.CharField(max_length=255)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return self.outcome_name


class LabLOContribution(models.Model):
    lab = models.ForeignKey(Lab, on_delete=models.CASCADE)
    learning_outcome = models.ForeignKey(LearningOutcome, on_delete=models.CASCADE)
    contribution_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.lab.lab_name} - {self.learning_outcome.outcome_description} - {self.semester.semester_name}"
