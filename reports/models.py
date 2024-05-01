# from django.db import models
# from courses.models import Class
# from django.utils import timezone


# # Create your models here.

# def get_submission_file_upload_path(instance, filename):
#     return f"{submission_files}/{instance.class_code.class_code}/{filename}"


# class SubmissionFile(models.Model):
#     file = models.FileField(upload_to=get_submission_file_upload_path)
#     class_code = models.ForeignKey(
#         Class, related_name="submission_class", on_delete=models.CASCADE
#     )
#     uploaded_at = models.DateTimeField(default=timezone.now)

#     def __str__(self):
#         return f"{self.file.name} - {self.class_code.class_code}"
