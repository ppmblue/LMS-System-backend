# from django.shortcuts import render
# from .serializers import SubmissionFileSerializer
# from courses.models import Class
# from .models import SubmissionFile
# from rest_framework import generics, parsers
# from django.shortcuts import get_object_or_404
# from rest_framework.permissions import IsAuthenticated
# from user_profiles.permissions import IsTeacher


# class SubmissionFile(generics.CreateAPIView):
#     lookup_url_kwarg = ["course_code", "class_code"]
#     permission_classes = IsAuthenticated, IsTeacher
#     queryset = SubmissionFile.objects.all()

#     def get_queryset(self):
#         return queryset.filter(class_code=self.kwargs.get("class_code"))

#     serializer_class = SubmissionFileSerializer
#     parser_classes = (parsers.FileUploadParser, parsers.MultiPartParser)


# # Create your views here.
