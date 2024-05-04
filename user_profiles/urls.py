from django.urls import path
from user_profiles import views

urlpatterns = [
    path("profile/", views.UserProfileDetail.as_view(), name="user-profile"),
    path("register/", views.RegisterAPIView.as_view(), name="register"),
]
