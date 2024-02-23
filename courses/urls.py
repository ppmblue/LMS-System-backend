from django.urls import path
from courses import views 

urlpatterns = [
    path('courses/', views.course_list, name='course-list'),
    path('courses/<int:pk>/', views.course_detail, name='course-detail'),
]

