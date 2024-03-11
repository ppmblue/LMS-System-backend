from django.urls import path
from courses import views

urlpatterns = [
    path("courses/", views.CourseList.as_view(), name="course-list"),
    path(
        "courses/<str:course_code>/", views.CourseDetail.as_view(), name="course-detail"
    ),
    path(
        "courses/<str:course_code>/semesters",
        views.CourseSemesterList.as_view(),
        name="semester-list",
    ),
    path(
        "courses/<str:course_code>/semesters/<str:semester_name>",
        views.CourseSemesterDetail.as_view(),
        name="semester-detail",
    ),
    path(
        "courses/<str:course_code>/teachers",
        views.CourseTeacherList.as_view(),
        name="teacher-list",
    ),
    path(
        "courses/<str:course_code>/teachers/<int:pk>",
        views.CourseTeacherDetail.as_view(),
        name="teacher-detail",
    ),
    path(
        "courses/<str:course_code>/semesters/<str:semester_name>/labs",
        views.LabList.as_view(),
        name="lab-list",
    ),
    path(
        "courses/<str:course_code>/semesters/<str:semester_name>/labs/<str:lab_pk>",
        views.LabDetail.as_view(),
        name="lab-detail",
    ),
    path(
        "courses/<str:course_code>/outcomes",
        views.LearningOutcomeList.as_view(),
        name="lo-list",
    ),
    path(
        "courses/<str:course_code>/outcomes/<str:outcome_code>",
        views.LearningOutcomeDetail.as_view(),
        name="lo-detail",
    ),
    path(
        "courses/<str:course_code>/semesters/<str:semester_name>/labs/<str:lab_pk>/contributions",
        views.LabLOList.as_view(),
        name="lab-lo-list",
    ),
    path(
        "courses/<str:course_code>/semesters/<str:semester_name>/labs/<str:lab_pk>/contributions/<str:outcome_code>",
        views.LabLODetail.as_view(),
        name="lab-lo-detail",
    ),
]
