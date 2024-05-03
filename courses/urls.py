from django.urls import path, include
from courses import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register("submission", views.SubmissionUploadForm, basename='upload')
router.register("exercise", views.ExerciseUploadForm, basename='upload')

urlpatterns = [
    path("courses/", views.CourseList.as_view(), name="course-list"),
    path(
        "courses/<str:course_code>/", views.CourseDetail.as_view(), name="course-detail"
    ),
    path(
        "courses/<str:course_code>/classes/",
        views.ClassListByCourse.as_view(),
        name="class-list-by-course",
    ),
    path(
        "courses/semesters",
        views.SemesterList.as_view(),
        name="class-semesters"  
    ),
    path(
        "courses/<str:course_code>/classes/<str:class_code>/",
        views.ClassDetail.as_view(),
        name="class-detail",
    ),
    path(
        "courses/<str:course_code>/classes/<str:class_code>/labs/",
        views.LabList.as_view(),
        name="lab-list",
    ),
    path(
        "courses/<str:course_code>/classes/<str:class_code>/labs/<str:lab_name>/",
        views.LabDetail.as_view(),
        name="lab-detail",
    ),
    path(
        "courses/<str:course_code>/outcomes/",
        views.LearningOutcomeList.as_view(),
        name="lo-list",
    ),
    path(
        "courses/<str:course_code>/outcomes/<str:outcome_code>/",
        views.LearningOutcomeDetail.as_view(),
        name="lo-detail",
    ),
    path(
        "courses/<str:course_code>/classes/<str:class_code>/labs/<str:lab_name>/contributions/",
        views.LabLOList.as_view(),
        name="contribution-list",
    ),
    path(
        "courses/<str:course_code>/classes/<str:class_code>/labs/<str:lab_name>/contributions/<str:outcome_code>/",
        views.LabLODetail.as_view(),
        name="contribution-detail",
    ),
    path("", include(router.urls)),
    path(
        "classes",
        views.ClassList.as_view(),
        name="classes"
    ),
    path(
        "classes/<str:class_code>/exercises/",
        views.ExerciseList.as_view(),
        name="exercise-list-by-class",
    ),
    path(
        "classes/<str:class_code>/exercises/<str:exercise_id>/",
        views.ExerciseDetail.as_view(),
        name="exercise-detail",
    ),
    path(
        "classes/<str:class_code>/submissions/",
        views.SubmissionList.as_view(),
        name="submission-list-by-class",
    )
]
