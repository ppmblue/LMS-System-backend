from django.db import models
from django.contrib.auth.models import AbstractUser


class UserProfile(AbstractUser):
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_teacher = models.BooleanField(default=False)
    # Additional fields for students
    student_id = models.CharField(max_length=20, blank=True, null=True)
    major = models.CharField(max_length=50, blank=True, null=True)
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["first_name", "email", "last_name"]

    def __str__(self):
        return f"{self.email}"

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="user_profiles_groups",
        blank=True,
        help_text="The groups this user belongs to. A user will get all permissions granted to these groups.",
        verbose_name="groups",
    )

    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="user_profiles_permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )
