from django.db import models

# Create your models here.
class Student(models.Model):
    last_name = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    student_id = models.IntegerField()
    secured_student_id = models.CharField(primary_key=True, max_length=200)