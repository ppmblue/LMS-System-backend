from django.db import models


from djongo.models import ArrayField, DjongoManager


class Course(models.Model):
    course_name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='course_images/', null=True, blank=True)
    department = models.CharField(max_length=255)

    objects = DjongoManager()