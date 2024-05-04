from django.urls import path
from user_profiles import views
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path("profile/", views.UserProfileDetail.as_view(), name="user-profile"),
    path("register/", views.RegisterAPIView.as_view(), name="register"),
    path("login/", views.Login.as_view(), name="login_token"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
