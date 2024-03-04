from django.urls import path
from courses import views

urlpatterns = [
    path("courses/", views.CourseList.as_view(), name="course-list"),
    path("courses/<int:pk>/", views.CourseDetail.as_view(), name="course-detail"),
    path(
        "courses/<int:pk>/semesters",
        views.CourseSemesterList.as_view(),
        name="semester-list",
    ),
    path(
        "courses/<int:course_pk>/semesters/<str:semester_name>",
        views.CourseSemesterDetail.as_view(),
        name="semester-detail",
    ),
    path(
        "courses/<int:pk>/teachers",
        views.CourseTeacherList.as_view(),
        name="teacher-list",
    ),
]
