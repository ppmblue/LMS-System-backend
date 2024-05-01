from django.urls import path, include
from courses import views
from rest_framework import routers

# router = routers.DefaultRouter()
# router.register("submission", views.SubmissionFile, basename="upload")

urlpatterns = [
    path("", views.CourseList.as_view(), name="course-list"),
    path("<str:course_code>/", views.CourseDetail.as_view(), name="course-detail"),
    path(
        "<str:course_code>/classes/",
        views.ClassListByCourse.as_view(),
        name="class-list-by-course",
    ),
    path("semesters/", views.SemesterList.as_view(), name="semesters"),
    path(
        "<str:course_code>/classes/<str:class_code>/",
        views.ClassDetail.as_view(),
        name="class-detail",
    ),
    path(
        "<str:course_code>/classes/<str:class_code>/labs/",
        views.LabList.as_view(),
        name="lab-list",
    ),
    path(
        "<str:course_code>/classes/<str:class_code>/labs/<str:lab_name>/",
        views.LabDetail.as_view(),
        name="lab-detail",
    ),
    path(
        "<str:course_code>/outcomes/",
        views.LearningOutcomeList.as_view(),
        name="lo-list",
    ),
    path(
        "<str:course_code>/outcomes/<str:outcome_code>/",
        views.LearningOutcomeDetail.as_view(),
        name="lo-detail",
    ),
    path(
        "<str:course_code>/classes/<str:class_code>/labs/<str:lab_name>/contributions/",
        views.LabLOList.as_view(),
        name="contribution-list",
    ),
    path(
        "<str:course_code>/classes/<str:class_code>/labs/<str:lab_name>/contributions/<str:outcome_code>/",
        views.LabLODetail.as_view(),
        name="contribution-detail",
    ),
    path(
        "<str:course_code>/classes/<str:class_code>/submissions/",
        views.UploadSubmissionFile.as_view(),
        name="upload-submission",
    ),
    # path("", include(router.urls)),
    # path("classes", views.ClassList.as_view(), name="classes"),
]
